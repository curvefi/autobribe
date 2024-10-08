import boa
import pytest


@pytest.fixture(scope="module")
def owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def fee_splitter_deployer():
    return boa.load_partial("contracts/FeeSplitter.vy")


@pytest.fixture(scope="module")
def mock_factory():
    return boa.load("tests/mocks/MockControllerFactory.vy")


@pytest.fixture(scope="module")
def mock_controller_deployer():
    return boa.load_partial("tests/mocks/MockController.vy")


@pytest.fixture(scope="module")
def mock_dynamic_weight_deployer():
    return boa.load_partial("tests/mocks/MockDynamicWeight.vy")


@pytest.fixture(scope="module", params=range(3))
def receivers(request, mock_dynamic_weight_deployer):
    receivers_possibilities = [
        [(mock_dynamic_weight_deployer().address, 10_000)],
        [(boa.env.generate_address(), 10_000)],
        [
            (boa.env.generate_address(), 7_000),
            (mock_dynamic_weight_deployer().address, 3_000),
        ],
    ]
    return receivers_possibilities[request.param]


@pytest.fixture(scope="module")
def fee_splitter(
    fee_splitter_deployer, crvusd, receivers, mock_factory, owner
):
    return fee_splitter_deployer(crvusd, mock_factory, receivers, owner)


@pytest.fixture(scope="module")
def fee_splitter_with_controllers(
    fee_splitter, mock_factory, mock_controller_deployer, crvusd
):
    mock_controllers = [mock_controller_deployer(crvusd) for _ in range(10)]
    for c in mock_controllers:
        mock_factory.add_controller(c)

    fee_splitter.update_controllers()
    return fee_splitter, mock_controllers
