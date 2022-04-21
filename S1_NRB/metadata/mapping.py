NRB_PATTERN = r'^(?P<sensor>S1[AB])_' \
              r'(?P<mode>IW|EW|S[1-6])_' \
              r'(?P<product>NRB)_' \
              r'(?P<resolution>_)' \
              r'(?P<processingLevel>1)' \
              r'(?P<category>S)' \
              r'(?P<pols>SH|SV|DH|DV)_' \
              r'(?P<start>[0-9]{8}T[0-9]{6})_' \
              r'(?P<orbitNumber>[0-9]{6})_' \
              r'(?P<dataTakeID>[0-9A-F]{6})_' \
              r'(?P<mgrsID>[0-9A-Z]{5})_' \
              r'(?P<ID>[0-9A-Z]{4})'

# 'z_error': Maximum error threshold on values for LERC* compression.
# Will be ignored if a compression algorithm is used that isn't related to LERC.
ITEM_MAP = {'VV_gamma0': {'suffix': 'vv-g-lin',
                          'z_error': 1e-4},
            'VH_gamma0': {'suffix': 'vh-g-lin',
                          'z_error': 1e-4},
            'HH_gamma0': {'suffix': 'hh-g-lin',
                          'z_error': 1e-4},
            'HV_gamma0': {'suffix': 'hv-g-lin',
                          'z_error': 1e-4},
            'incidenceAngleFromEllipsoid': {'suffix': 'ei',
                                            'z_error': 1e-3},
            'layoverShadowMask': {'suffix': 'dm',
                                  'z_error': 0.0},
            'localIncidenceAngle': {'suffix': 'li',
                                    'z_error': 1e-2},
            'scatteringArea': {'suffix': 'lc',
                               'z_error': 0.1},
            'gammaSigmaRatio': {'suffix': 'gs',
                                'z_error': 1e-4},
            'acquisitionImage': {'suffix': 'id',
                                 'z_error': 0.0},
            'VV_NESZ': {'suffix': 'np-vv',
                        'z_error': 2e-5},
            'VH_NESZ': {'suffix': 'np-vh',
                        'z_error': 2e-5},
            'HH_NESZ': {'suffix': 'np-hh',
                        'z_error': 2e-5},
            'HV_NESZ': {'suffix': 'np-hv',
                        'z_error': 2e-5}}

# Source data resolution
# https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-1-sar/products-algorithms/level-1-algorithms/single-look-complex
RES_MAP = {'IW': {'azimuthResolution': {'IW1': 22.5,
                                        'IW2': 22.7,
                                        'IW3': 22.6},
                  'rangeResolution': {'IW1': 2.7,
                                      'IW2': 3.1,
                                      'IW3': 3.5}},
           'EW': {'azimuthResolution': {'EW1': 43.7,
                                        'EW2': 44.3,
                                        'EW3': 45.2,
                                        'EW4': 45.6,
                                        'EW5': 44.0},
                  'rangeResolution': {'EW1': 7.9,
                                      'EW2': 9.9,
                                      'EW3': 11.6,
                                      'EW4': 13.3,
                                      'EW5': 14.4}},
           'SM': {'azimuthResolution': {'S1': 4.9,
                                        'S2': 4.9,
                                        'S3': 4.9,
                                        'S4': 4.9,
                                        'S5': 3.9,
                                        'S6': 4.9},
                  'rangeResolution': {'S1': 1.7,
                                      'S2': 2.0,
                                      'S3': 2.5,
                                      'S4': 3.3,
                                      'S5': 3.3,
                                      'S6': 3.6}}
           }

ORB_MAP = {'PREORB': 'predicted',
           'RESORB': 'restituted',
           'POEORB': 'precise'}

DEM_MAP = {
    'GETASSE30':
        {'access': 'https://step.esa.int/auxdata/dem/GETASSE30',
         'ref': 'https://seadas.gsfc.nasa.gov/help-8.1.0/desktop/GETASSE30ElevationModel.html',
         'type': 'elevation',
         'egm': 'https://apps.dtic.mil/sti/citations/ADA166519'},
    'Copernicus 10m EEA DEM':
        {'access': 'ftps://cdsdata.copernicus.eu/DEM-datasets/COP-DEM_EEA-10-DGED/2021_1',
         'ref': 'https://spacedata.copernicus.eu/web/cscda/dataset-details?articleId=394198',
         'type': 'surface',
         'egm': 'https://bgi.obs-mip.fr/data-products/grids-and-models/egm2008-global-model/'},
    'Copernicus 30m Global DEM':
        {'access': 'https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/',
         'ref': 'https://copernicus-dem-30m.s3.amazonaws.com/readme.html',
         'type': 'surface',
         'egm': 'https://bgi.obs-mip.fr/data-products/grids-and-models/egm2008-global-model/'},
    'Copernicus 30m Global DEM II':
        {'access': 'ftps://cdsdata.copernicus.eu/DEM-datasets/COP-DEM_GLO-30-DGED/2021_1',
         'ref': 'https://spacedata.copernicus.eu/web/cscda/dataset-details?articleId=394198',
         'type': 'surface',
         'egm': 'https://bgi.obs-mip.fr/data-products/grids-and-models/egm2008-global-model/'},
    'Copernicus 90m Global DEM II':
        {'access': 'ftps://cdsdata.copernicus.eu/DEM-datasets/COP-DEM_GLO-90-DGED/2021_1',
         'ref': 'https://spacedata.copernicus.eu/web/cscda/dataset-details?articleId=394198',
         'type': 'surface',
         'egm': 'https://bgi.obs-mip.fr/data-products/grids-and-models/egm2008-global-model/'}
    }

NS_MAP = {'nrb': {'source': 'http://earth.esa.int/sentinel-1/nrb/source/1.0',
                  'product': 'http://earth.esa.int/sentinel-1/nrb/product/1.0'},
          'sar': 'http://www.opengis.net/sar/2.1',
          'eop': 'http://www.opengis.net/eop/2.1',
          'om': 'http://www.opengis.net/om/2.0',
          'gml': 'http://www.opengis.net/gml/3.2',
          'ows': 'http://www.opengis.net/ows/2.0',
          'xlink': 'http://www.w3.org/1999/xlink'}

SAMPLE_MAP = {'-dm.tif': {'type': 'Mask',
                          'unit': None,
                          'role': 'data-mask',
                          'title': 'Data Mask Image',
                          'values': {0: 'not layover, nor shadow',
                                     1: 'layover',
                                     2: 'shadow',
                                     3: 'layover and shadow',
                                     4: 'ocean water'}},
              '-ei.tif': {'type': 'Angle',
                          'unit': 'deg',
                          'role': 'ellipsoid-incidence-angle',
                          'title': 'Ellipsoid Incidence Angle'},
              '-lc.tif': {'type': 'Scattering Area',
                          'unit': 'square_meters',
                          'role': 'contributing-area',
                          'title': 'Local Contributing Area'},
              '-li.tif': {'type': 'Angle',
                          'unit': 'deg',
                          'role': 'local-incidence-angle',
                          'title': 'Local Incidence Angle'},
              '-gs.tif': {'type': 'Ratio',
                          'unit': None,
                          'role': 'gamma-sigma-ratio',
                          'title': 'Gamma0 RTC to sigma0 RTC ratio'},
              '-id.tif': {'type': 'AcqID',
                          'unit': None,
                          'role': 'acquisition-id',
                          'title': 'Acquisition ID Image'},
              '-np-[vh]{2}.tif': {'type': 'Sigma-0',
                                  'unit': 'dB',
                                  'role': 'noise-power',
                                  'title': 'Noise Power'}}
