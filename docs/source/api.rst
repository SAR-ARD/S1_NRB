API Documentation
=================

Configuration
-------------

.. automodule:: S1_NRB.config
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        gdal_conf
        snap_conf
        get_config

Processing
----------

.. automodule:: S1_NRB.processor
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        main

SNAP
^^^^

.. automodule:: S1_NRB.snap
    :members:
    :undoc-members:
    :show-inheritance:

    .. rubric:: core processing

    .. autosummary::
        :nosignatures:

        process
        geo
        grd_buffer
        gsr
        mli
        pre
        rtc
        sgr
        look_direction

    .. rubric:: ancillary functions

    .. autosummary::
        :nosignatures:

        find_datasets
        get_metadata
        postprocess
        nrt_slice_num

ARD
^^^

.. automodule:: S1_NRB.ard
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        calc_product_start_stop
        create_acq_id_image
        create_data_mask
        create_rgb_vrt
        create_vrt
        format
        get_datasets
        wind_normalization

ETAD
^^^^

.. automodule:: S1_NRB.etad
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        process

DEM
^^^

.. automodule:: S1_NRB.dem
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        mosaic
        prepare

OCN
^^^

.. automodule:: S1_NRB.ocn
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        extract
        gapfill

Tile Extraction
---------------

.. automodule:: S1_NRB.tile_extraction
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        aoi_from_scene
        aoi_from_tile
        description2dict
        tile_from_aoi

Ancillary Functions
-------------------

.. automodule:: S1_NRB.ancillary
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        buffer_min_overlap
        check_scene_consistency
        check_spacing
        generate_unique_id
        get_max_ext
        group_by_time
        log
        set_logging
        vrt_add_overviews

Scene Search
------------

.. automodule:: S1_NRB.search
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        ASF
        ASFArchive
        STACArchive
        asf_select
        check_acquisition_completeness
        collect_neighbors
        scene_select

Metadata
--------

Extraction
^^^^^^^^^^

.. automodule:: S1_NRB.metadata.extract
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        calc_enl
        calc_geolocation_accuracy
        calc_performance_estimates
        calc_pslr_islr
        copy_src_meta
        find_in_annotation
        geometry_from_vec
        get_header_size
        get_prod_meta
        get_src_meta
        meta_dict

XML
^^^

.. automodule:: S1_NRB.metadata.xml
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        parse
        product_xml
        source_xml

STAC
^^^^

.. automodule:: S1_NRB.metadata.stac
    :members:
    :undoc-members:
    :show-inheritance:

    .. autosummary::
        :nosignatures:

        parse
        product_json
        source_json
        make_catalog
