def test_import_smoke():
    import pyntlp

    assert callable(pyntlp.load_params)
    assert callable(pyntlp.compute_pma_sso)
    assert callable(pyntlp.build_lga_segment_metrics)
