def test_import_smoke():
    import pyntlp

    assert callable(pyntlp.load_params)
    assert callable(pyntlp.compute_pma_sso)

