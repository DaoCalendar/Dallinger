import yaml


def test_get_docker_compose_yml_extra_config():
    """Make sure all values passed in config make their way to the
    web and worker container environment
    """
    result = get_yaml({"foo": "bar"})
    assert result["services"]["web"]["environment"]["foo"] == "bar"


def test_get_docker_compose_yml_core_config():
    """Make sure worker and web services have the necessary variables to run"""
    result = get_yaml({})
    assert "REDIS_URL" in result["services"]["worker"]["environment"]
    assert "DATABASE_URL" in result["services"]["worker"]["environment"]
    assert "HOME" in result["services"]["worker"]["environment"]


def test_get_docker_compose_yml_env_vars_always_strings():
    """The docker-compose.yml file we generate should always have strings as
    values in the `environment` section of each service.
    """
    result = get_yaml({"foo": True, "bar": 2})
    assert result["services"]["worker"]["environment"]["foo"] == "True"
    assert result["services"]["worker"]["environment"]["bar"] == "2"


def test_get_docker_compose_yml_env_vars_escaping():
    """Environment vars with special character should be correctly escaped."""
    result = get_yaml(
        {
            "foo": r'" a quote and a \ backslash ',
        }
    )
    assert (
        result["services"]["worker"]["environment"]["foo"]
        == r'" a quote and a \ backslash '
    )


def get_yaml(config):
    from dallinger.command_line.docker_ssh import get_docker_compose_yml

    yaml_contents = get_docker_compose_yml(
        config, "dlgr-8c43a887", "ghcr.io/dallinger/dallinger/bartlett1932", "foobar"
    )
    return yaml.load(yaml_contents)