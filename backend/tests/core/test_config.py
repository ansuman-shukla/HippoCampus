def test_configuration_loading():
    config = load_config('path/to/config/file')
    assert config is not None
    assert config['setting1'] == 'default_value1'
    assert config['setting2'] == 'default_value2'