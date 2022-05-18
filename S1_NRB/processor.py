import os
import re
import time
from osgeo import gdal
from spatialist import Vector
from spatialist.ancillary import finder
from pyroSAR import identify_many, Archive
from pyroSAR.snap.util import geocode, noise_power
from pyroSAR.ancillary import groupbyTime, seconds
from S1_NRB import etad, dem, nrb
from S1_NRB.config import get_config, geocode_conf, gdal_conf
from S1_NRB.ancillary import set_logging, log
import S1_NRB.tile_extraction as tile_ex

gdal.UseExceptions()


def main(config_file, section_name='GENERAL', debug=False):
    """
    Main function that initiates and controls the processing workflow.
    
    Parameters
    ----------
    config_file: str
        Full path to a `config.ini` file.
    section_name: str, optional
        Section name of the `config.ini` file that parameters should be parsed from. Default is 'GENERAL'.
    debug: bool, optional
        Set pyroSAR logging level to DEBUG? Default is False.
    """
    config = get_config(config_file=config_file, section_name=section_name)
    logger = set_logging(config=config, debug=debug)
    geocode_prms = geocode_conf(config=config)
    gdal_prms = gdal_conf(config=config)
    
    snap_flag = True
    nrb_flag = True
    if config['mode'] == 'snap':
        nrb_flag = False
    elif config['mode'] == 'nrb':
        snap_flag = False
    
    ####################################################################################################################
    # archive / scene selection
    scenes = finder(config['scene_dir'], [r'^S1[AB].*\.zip$'], regex=True, recursive=True)
    
    if config['acq_mode'] == 'SM':
        acq_mode_search = ('S1', 'S2', 'S3', 'S4', 'S5', 'S6')
    else:
        acq_mode_search = config['acq_mode']
    
    if config['aoi_tiles'] is not None:
        vec = tile_ex.aoi_from_tiles(kml=config['kml_file'], tiles=config['aoi_tiles'])
    else:
        vec = Vector(config['aoi_geometry'])
    
    with Archive(dbfile=config['db_file']) as archive:
        archive.insert(scenes)
        selection = archive.select(vectorobject=vec,
                                   product=config['product'],
                                   acquisition_mode=acq_mode_search,
                                   mindate=config['mindate'], maxdate=config['maxdate'])
    del vec
    
    if len(selection) == 0:
        message = "No scenes could be found for acquisition mode '{acq_mode}', " \
                  "mindate '{mindate}' and maxdate '{maxdate}' in directory '{scene_dir}'."
        raise RuntimeError(message.format(acq_mode=config['acq_mode'], mindate=config['mindate'],
                                          maxdate=config['maxdate'], scene_dir=config['scene_dir']))
    ids = identify_many(selection)
    
    ####################################################################################################################
    # general setup
    geo_dict = tile_ex.get_tile_dict(config=config, spacing=geocode_prms['spacing'])
    aoi_tiles = list(geo_dict.keys())
    aoi_tiles.remove('align')
    
    epsg_set = set([geo_dict[tile]['epsg'] for tile in list(geo_dict.keys()) if tile != 'align'])
    if len(epsg_set) != 1:
        raise RuntimeError('The AOI covers multiple UTM zones: {}\n '
                           'This is currently not supported. '
                           'Please refine your AOI.'.format(list(epsg_set)))
    epsg = epsg_set.pop()
    
    np_dict = {'sigma0': 'NESZ', 'beta0': 'NEBZ', 'gamma0': 'NEGZ'}
    np_refarea = 'sigma0'
    
    ####################################################################################################################
    # DEM download and MGRS-tiling
    if snap_flag:
        geometries = [scene.bbox() for scene in ids]
        dem.prepare(geometries=geometries, threads=gdal_prms['threads'],
                    epsg=epsg, spacing=geocode_prms['spacing'],
                    dem_dir=config['dem_dir'], wbm_dir=config['wbm_dir'],
                    dem_type=config['dem_type'], kml_file=config['kml_file'])
        del geometries
        
        if config['dem_type'] == 'Copernicus 30m Global DEM':
            ex_dem_nodata = -99
        else:
            ex_dem_nodata = None
    
    ####################################################################################################################
    # SNAP RTC processing
    if snap_flag:
        for i, scene in enumerate(ids):
            ###############################################
            scene_base = os.path.splitext(os.path.basename(scene.scene))[0]
            out_dir_scene = os.path.join(config['rtc_dir'], scene_base)
            tmp_dir_scene = os.path.join(config['tmp_dir'], scene_base)
            out_dir_scene_epsg = os.path.join(out_dir_scene, str(epsg))
            tmp_dir_scene_epsg = os.path.join(tmp_dir_scene, str(epsg))
            os.makedirs(out_dir_scene_epsg, exist_ok=True)
            os.makedirs(tmp_dir_scene_epsg, exist_ok=True)
            fname_dem = os.path.join(tmp_dir_scene_epsg,
                                     scene.outname_base() + '_DEM_{}.tif'.format(epsg))
            ###############################################
            # scene-specific DEM preparation
            with scene.bbox() as geometry:
                dem.mosaic(geometry, outname=fname_dem, epsg=epsg,
                           dem_type=config['dem_type'], kml_file=config['kml_file'],
                           dem_dir=config['dem_dir'])
            ###############################################
            # ETAD correction
            if config['etad']:
                print('###### [   ETAD] Scene {s}/{s_total}: {scene}'.format(s=i + 1, s_total=len(ids),
                                                                             scene=scene.scene))
                scene = etad.process(scene=scene, etad_dir=config['etad_dir'],
                                     out_dir=tmp_dir_scene, log=logger)
            ###############################################
            if scene.product == 'SLC':
                rlks = {'IW': 5,
                        'SM': 6,
                        'EW': 3}[config['acq_mode']]
                azlks = {'IW': 1,
                         'SM': 6,
                         'EW': 1}[config['acq_mode']]
            else:
                rlks = azlks = None
            
            # SLC SM noise removal is currently not possible with SNAP
            # see https://forum.step.esa.int/t/stripmap-slc-error-during-thermal-noise-removal/32688
            remove_noise = True
            if scene.product == 'SLC' and re.search('S[1-6]', scene.acquisition_mode):
                remove_noise = False
            ###############################################
            list_processed = finder(out_dir_scene_epsg, ['*'])
            exclude = list(np_dict.values())
            print('###### [GEOCODE] Scene {s}/{s_total}: {scene}'.format(s=i + 1, s_total=len(ids),
                                                                         scene=scene.scene))
            if len([item for item in list_processed if not any(ex in item for ex in exclude)]) < 4:
                start_time = time.time()
                try:
                    geocode(infile=scene, outdir=out_dir_scene_epsg, t_srs=epsg, tmpdir=tmp_dir_scene_epsg,
                            standardGridOriginX=geo_dict['align']['xmax'],
                            standardGridOriginY=geo_dict['align']['ymin'],
                            externalDEMFile=fname_dem, externalDEMNoDataValue=ex_dem_nodata,
                            rlks=rlks, azlks=azlks, **geocode_prms, removeS1ThermalNoise=remove_noise)
                    t = round((time.time() - start_time), 2)
                    log(handler=logger, mode='info', proc_step='GEOCODE', scenes=scene.scene, epsg=epsg, msg=t)
                    if t <= 500:
                        msg = 'Processing might have terminated prematurely. Check terminal for uncaught SNAP errors!'
                        log(handler=logger, mode='warning', proc_step='GEOCODE', scenes=scene.scene, epsg=epsg, msg=msg)
                except Exception as e:
                    log(handler=logger, mode='exception', proc_step='GEOCODE', scenes=scene.scene, epsg=epsg, msg=e)
                    continue
            else:
                msg = 'Already processed - Skip!'
                print('### ' + msg)
                log(handler=logger, mode='info', proc_step='GEOCODE', scenes=scene.scene, epsg=epsg, msg=msg)
            ###############################################
            if not remove_noise:
                continue
            print('###### [NOISE_P] Scene {s}/{s_total}: {scene}'.format(s=i + 1, s_total=len(ids),
                                                                         scene=scene.scene))
            if len([item for item in list_processed if np_dict[np_refarea] in item]) == 0:
                start_time = time.time()
                try:
                    noise_power(infile=scene.scene, outdir=out_dir_scene_epsg, polarizations=scene.polarizations,
                                spacing=geocode_prms['spacing'], refarea=np_refarea, tmpdir=tmp_dir_scene_epsg,
                                externalDEMFile=fname_dem, externalDEMNoDataValue=ex_dem_nodata, t_srs=epsg,
                                externalDEMApplyEGM=geocode_prms['externalDEMApplyEGM'],
                                alignToStandardGrid=geocode_prms['alignToStandardGrid'],
                                standardGridOriginX=geo_dict['align']['xmax'],
                                standardGridOriginY=geo_dict['align']['ymin'],
                                clean_edges=geocode_prms['clean_edges'],
                                clean_edges_npixels=geocode_prms['clean_edges_npixels'],
                                rlks=rlks, azlks=rlks)
                    log(handler=logger, mode='info', proc_step='NOISE_P', scenes=scene.scene, epsg=epsg,
                        msg=round((time.time() - start_time), 2))
                except Exception as e:
                    log(handler=logger, mode='exception', proc_step='NOISE_P', scenes=scene.scene, epsg=epsg, msg=e)
                    continue
            else:
                msg = 'Already processed - Skip!'
                print('### ' + msg)
                log(handler=logger, mode='info', proc_step='NOISE_P', scenes=scene.scene, epsg=epsg, msg=msg)
    
    ####################################################################################################################
    # NRB - final product generation
    if nrb_flag:
        selection_grouped = groupbyTime(images=selection, function=seconds, time=60)
        for t, tile in enumerate(aoi_tiles):
            outdir = os.path.join(config['nrb_dir'], tile)
            os.makedirs(outdir, exist_ok=True)
            wbm = os.path.join(config['wbm_dir'], config['dem_type'], '{}_WBM.tif'.format(tile))
            if not os.path.isfile(wbm):
                wbm = None
            
            for s, scenes in enumerate(selection_grouped):
                if isinstance(scenes, str):
                    scenes = [scenes]
                print('###### [    NRB] Tile {t}/{t_total}: {tile} | '
                      'Scenes {s}/{s_total}: {scenes} '.format(tile=tile, t=t + 1, t_total=len(aoi_tiles),
                                                               scenes=[os.path.basename(s) for s in scenes],
                                                               s=s + 1, s_total=len(selection_grouped)))
                try:
                    msg = nrb.format(config=config, scenes=scenes, datadir=config['rtc_dir'], outdir=outdir,
                                     tile=tile, extent=geo_dict[tile]['ext'], epsg=epsg, wbm=wbm,
                                     multithread=gdal_prms['multithread'])
                    if msg == 'Already processed - Skip!':
                        print('### ' + msg)
                    log(handler=logger, mode='info', proc_step='NRB', scenes=scenes, epsg=epsg, msg=msg)
                except Exception as e:
                    log(handler=logger, mode='exception', proc_step='NRB', scenes=scenes, epsg=epsg, msg=e)
                    continue
        gdal.SetConfigOption('GDAL_NUM_THREADS', gdal_prms['threads_before'])
