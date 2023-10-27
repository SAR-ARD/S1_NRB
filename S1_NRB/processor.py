import os
import time
from osgeo import gdal
from spatialist import Vector, bbox, intersect
from spatialist.ancillary import finder
from pyroSAR import identify_many, Archive
from S1_NRB import etad, dem, ard, snap
from S1_NRB.config import get_config, snap_conf, gdal_conf
import S1_NRB.ancillary as anc
import S1_NRB.tile_extraction as tile_ex
from S1_NRB.archive import STACArchive
from datetime import datetime, timedelta
from S1_NRB import ocn

gdal.UseExceptions()


def main(config_file, section_name='PROCESSING', debug=False, **kwargs):
    """
    Main function that initiates and controls the processing workflow.
    
    Parameters
    ----------
    config_file: str
        Full path to a `config.ini` file.
    section_name: str
        Section name of the `config.ini` file that processing parameters
        should be parsed from. Default is 'PROCESSING'.
    debug: bool
        Set pyroSAR logging level to DEBUG? Default is False.
    **kwargs
        extra arguments to override parameters in the config file. E.g. `acq_mode`.
    """
    update = False  # update existing products? Internal development flag.
    config = get_config(config_file=config_file, proc_section=section_name, **kwargs)
    logger = anc.set_logging(config=config, debug=debug)
    geocode_prms = snap_conf(config=config)
    gdal_prms = gdal_conf(config=config)
    
    anc.check_spacing(geocode_prms['spacing'])
    
    sar_flag = 'sar' in config['mode']
    nrb_flag = 'nrb' in config['mode']
    orb_flag = 'orb' in config['mode']
    
    # DEM download authentication
    username, password = dem.authenticate(dem_type=config['dem_type'],
                                          username=None, password=None)
    ####################################################################################################################
    # archive / scene selection
    if config['acq_mode'] == 'SM':
        acq_mode_search = ('S1', 'S2', 'S3', 'S4', 'S5', 'S6')
    else:
        acq_mode_search = config['acq_mode']
    
    vec = None
    aoi_tiles = None
    selection = []
    if config['aoi_tiles'] is not None:
        vec = tile_ex.aoi_from_tile(kml=config['kml_file'], tile=config['aoi_tiles'])
        if not isinstance(vec, list):
            vec = [vec]
        aoi_tiles = config['aoi_tiles']
    elif config['aoi_geometry'] is not None:
        vec = [Vector(config['aoi_geometry'])]
        aoi_tiles = tile_ex.tile_from_aoi(vector=vec[0], kml=config['kml_file'])
    
    if config['datatake'] is not None:
        datatake = [int(x, 16) for x in config['datatake']]
    else:
        datatake = None
    
    if config['db_file'] is not None:
        scenes = finder(config['scene_dir'], [r'^S1[AB].*(SAFE|zip)$'],
                        regex=True, recursive=True, foldermode=1)
        archive = Archive(dbfile=config['db_file'])
        archive.insert(scenes)
    else:
        archive = STACArchive(url=config['stac_catalog'],
                              collections=config['stac_collections'])
    
    # derive geometries and tiles from scene footprints
    if vec is None:
        selection_tmp = archive.select(sensor=config['sensor'],
                                       vectorobject=None,
                                       product=config['product'],
                                       acquisition_mode=acq_mode_search,
                                       mindate=config['mindate'],
                                       maxdate=config['maxdate'],
                                       frameNumber=datatake,
                                       date_strict=config['date_strict'])
        scenes = identify_many(scenes=selection_tmp)
        scenes_geom = [x.geometry() for x in scenes]
        # select all tiles overlapping with the scenes for further processing
        vec = tile_ex.tile_from_aoi(vector=scenes_geom, kml=config['kml_file'],
                                    return_geometries=True)
        aoi_tiles = [x.mgrs for x in vec]
        del scenes_geom, scenes
        # extend the time range to fully cover all tiles
        # (one additional scene needed before and after each data take group)
        mindate = config['mindate'] - timedelta(minutes=1)
        maxdate = config['maxdate'] + timedelta(minutes=1)
    else:
        mindate = config['mindate']
        maxdate = config['maxdate']
    
    for item in vec:
        selection.extend(
            archive.select(sensor=config['sensor'],
                           vectorobject=item,
                           product=config['product'],
                           acquisition_mode=acq_mode_search,
                           mindate=mindate,
                           maxdate=maxdate,
                           frameNumber=datatake,
                           date_strict=config['date_strict']))
    selection = list(set(selection))
    del vec
    
    if len(selection) == 0:
        msg = "No scenes could be found for the following search query:\n" \
              " sensor:      '{sensor}'\n" \
              " product:     '{product}'\n" \
              " acq. mode:   '{acq_mode}'\n" \
              " mindate:     '{mindate}'\n" \
              " maxdate:     '{maxdate}'\n" \
              " date_strict: '{date_strict}'\n" \
              " datatake:    '{datatake}'\n"
        print(msg.format(sensor=config['sensor'], acq_mode=config['acq_mode'],
                         product=config['product'], mindate=config['mindate'],
                         maxdate=config['maxdate'], date_strict=config['date_strict'],
                         datatake=config['datatake']))
        archive.close()
        return
    print('found the following scene(s):')
    print('\n'.join(selection))
    scenes = identify_many(selection, sortkey='start')
    anc.check_acquisition_completeness(scenes=scenes, archive=archive)
    
    # OCN scene selection
    if 'wm' in config['annotation']:
        basenames = [x.outname_base() for x in scenes]
        scenes_ocn = archive.select(product='OCN', outname_base=basenames)
        if len(scenes_ocn) != len(scenes):
            print('could not find an OCN product for each selected Level-1 product')
            archive.close()
            return
        scenes_ocn = identify_many(scenes_ocn)
    else:
        scenes_ocn = []
    
    archive.close()
    
    if aoi_tiles is None:
        vec = [x.bbox() for x in scenes]
        aoi_tiles = tile_ex.tile_from_aoi(vector=vec, kml=config['kml_file'])
        del vec
    ####################################################################################################################
    # annotation layer selection
    annotation = config.get('annotation', None)
    measurement = config['measurement']
    export_extra = None
    lookup = {'dm': 'layoverShadowMask',
              'ei': 'incidenceAngleFromEllipsoid',
              'lc': 'scatteringArea',
              'ld': 'lookDirection',
              'li': 'localIncidenceAngle',
              'np': 'NESZ',
              'gs': 'gammaSigmaRatio',
              'sg': 'sigmaGammaRatio'}
    
    if annotation is not None:
        annotation = ['gs' if x == 'ratio' and measurement == 'gamma' else 'sg' if x == 'ratio'
        else x for x in annotation]
        export_extra = []
        for layer in annotation:
            if layer in lookup:
                export_extra.append(lookup[layer])
    
    ####################################################################################################################
    # main SAR processing
    if sar_flag:
        for i, scene in enumerate(scenes):
            scene_base = os.path.splitext(os.path.basename(scene.scene))[0]
            out_dir_scene = os.path.join(config['sar_dir'], scene_base)
            tmp_dir_scene = os.path.join(config['tmp_dir'], scene_base)
            
            print(f'###### [    SAR] Scene {i + 1}/{len(scenes)}: {scene.scene}')
            if os.path.isdir(out_dir_scene) and not update:
                msg = 'Already processed - Skip!'
                print('### ' + msg)
                anc.log(handler=logger, mode='info', proc_step='GEOCODE', scenes=scene.scene, msg=msg)
                continue
            else:
                os.makedirs(out_dir_scene, exist_ok=True)
                os.makedirs(tmp_dir_scene, exist_ok=True)
            ############################################################################################################
            # Preparation of DEM for SAR processing
            dem_type_lookup = {'Copernicus 10m EEA DEM': 'EEA10',
                               'Copernicus 30m Global DEM II': 'GLO30II',
                               'Copernicus 30m Global DEM': 'GLO30',
                               'GETASSE30': 'GETASSE30'}
            dem_type_short = dem_type_lookup[config['dem_type']]
            fname_base_dem = scene_base + f'_DEM_{dem_type_short}.tif'
            fname_dem = os.path.join(tmp_dir_scene, fname_base_dem)
            os.makedirs(tmp_dir_scene, exist_ok=True)
            print('###### [    DEM] creating scene-specific mosaic:', fname_dem)
            with scene.bbox() as geom:
                dem.mosaic(geometry=geom, outname=fname_dem, dem_type=config['dem_type'],
                           username=username, password=password)
            ############################################################################################################
            # ETAD correction
            if config['etad']:
                msg = '###### [   ETAD] Scene {s}/{s_total}: {scene}'
                print(msg.format(s=i + 1, s_total=len(scenes), scene=scene.scene))
                scene = etad.process(scene=scene, etad_dir=config['etad_dir'],
                                     out_dir=tmp_dir_scene, log=logger)
            ############################################################################################################
            # determination of look factors
            if scene.product == 'SLC':
                rlks = {'IW': 5,
                        'SM': 6,
                        'EW': 3}[config['acq_mode']]
                rlks *= int(geocode_prms['spacing'] / 10)
                azlks = {'IW': 1,
                         'SM': 6,
                         'EW': 1}[config['acq_mode']]
                azlks *= int(geocode_prms['spacing'] / 10)
            else:
                rlks = azlks = None
            ############################################################################################################
            # get neighbouring GRD scenes to add a buffer to the geocoded scenes
            # otherwise there will be a gap between final geocoded images.
            neighbors = None
            if scene.product == 'GRD':
                print('###### [    SAR] collecting GRD neighbors')
                f = '%Y%m%dT%H%M%S'
                td = timedelta(seconds=2)
                start = datetime.strptime(scene.start, f) - td
                start = datetime.strftime(start, f)
                stop = datetime.strptime(scene.stop, f) + td
                stop = datetime.strftime(stop, f)
                
                if config['db_file'] is not None:
                    archive = Archive(dbfile=config['db_file'])
                else:
                    archive = STACArchive(url=config['stac_catalog'],
                                          collections=config['stac_collections'])
                
                neighbors = archive.select(mindate=start, maxdate=stop, date_strict=False,
                                           sensor=scene.sensor, product=scene.product,
                                           acquisition_mode=scene.acquisition_mode)
                archive.close()
                del neighbors[neighbors.index(scene.scene)]
            ############################################################################################################
            # main processing routine
            start_time = time.time()
            try:
                snap.process(scene=scene.scene, outdir=config['sar_dir'],
                             measurement=measurement,
                             tmpdir=config['tmp_dir'], kml=config['kml_file'],
                             dem=fname_dem, neighbors=neighbors,
                             export_extra=export_extra,
                             gpt_args=config['snap_gpt_args'],
                             rlks=rlks, azlks=azlks, **geocode_prms)
                t = round((time.time() - start_time), 2)
                anc.log(handler=logger, mode='info', proc_step='SAR', scenes=scene.scene, msg=t)
            except Exception as e:
                anc.log(handler=logger, mode='exception', proc_step='SAR', scenes=scene.scene, msg=e)
                raise
    ####################################################################################################################
    # OCN preparation
    for scene in scenes_ocn:
        if scene.compression is not None:
            scene.unpack(directory=config['tmp_dir'], exist_ok=True)
        basename = os.path.basename(scene.scene).replace('.SAFE', '')
        outdir = os.path.join(config['sar_dir'], basename)
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, 'owiNrcsCmod.tif')
        if not os.path.isfile(out):
            ocn.extract(src=scene.scene, dst=out,
                        variable='owiNrcsCmod')
    ####################################################################################################################
    # ARD - final product generation
    if nrb_flag or orb_flag:
        product_type = 'NRB' if nrb_flag else 'ORB'
        
        # prepare WBM MGRS tiles
        vec = [x.geometry() for x in scenes]
        extent = anc.get_max_ext(geometries=vec)
        del vec
        with bbox(coordinates=extent, crs=4326) as box:
            dem.prepare(vector=box, threads=gdal_prms['threads'],
                        dem_dir=None, wbm_dir=config['wbm_dir'],
                        dem_type=config['dem_type'], kml_file=config['kml_file'],
                        tilenames=aoi_tiles, username=username, password=password,
                        dem_strict=True)
        print('preparing {} products'.format(product_type))
        selection_grouped = anc.group_by_time(scenes=scenes)
        for s, group in enumerate(selection_grouped):
            # check that the scenes can really be grouped together
            anc.check_scene_consistency(scenes=group)
            # get the geometries of all tiles that overlap with the current scene group
            vec = [x.geometry() for x in group]
            tiles = tile_ex.tile_from_aoi(vector=vec,
                                          kml=config['kml_file'],
                                          return_geometries=True,
                                          tilenames=aoi_tiles)
            del vec
            t_total = len(tiles)
            s_total = len(selection_grouped)
            for t, tile in enumerate(tiles):
                # select all scenes from the group whose footprint overlaps with the current tile
                scenes_sub = [x for x in group if intersect(tile, x.geometry())]
                scenes_sub_fnames = [x.scene for x in scenes_sub]
                outdir = os.path.join(config['ard_dir'], tile.mgrs)
                os.makedirs(outdir, exist_ok=True)
                fname_wbm = os.path.join(config['wbm_dir'], config['dem_type'],
                                         '{}_WBM.tif'.format(tile.mgrs))
                if not os.path.isfile(fname_wbm):
                    fname_wbm = None
                add_dem = True  # add the DEM as output layer?
                dem_type = config['dem_type'] if add_dem else None
                extent = tile.extent
                epsg = tile.getProjection('epsg')
                msg = '###### [    {product_type}] Tile {t}/{t_total}: {tile} | Scenes: {scenes} '
                print(msg.format(tile=tile.mgrs, t=t + 1, t_total=t_total,
                                 scenes=[os.path.basename(s) for s in scenes_sub_fnames],
                                 product_type=product_type, s=s + 1, s_total=s_total))
                try:
                    msg = ard.format(config=config, product_type=product_type, scenes=scenes_sub_fnames,
                                     datadir=config['sar_dir'], outdir=outdir, tile=tile.mgrs, extent=extent, epsg=epsg,
                                     wbm=fname_wbm, dem_type=dem_type, kml=config['kml_file'],
                                     multithread=gdal_prms['multithread'], annotation=annotation, update=update)
                    if msg == 'Already processed - Skip!':
                        print('### ' + msg)
                    anc.log(handler=logger, mode='info', proc_step=product_type, scenes=scenes_sub_fnames, msg=msg)
                except Exception as e:
                    anc.log(handler=logger, mode='exception', proc_step=product_type, scenes=scenes_sub_fnames, msg=e)
                    raise
            del tiles
        gdal.SetConfigOption('GDAL_NUM_THREADS', gdal_prms['threads_before'])
