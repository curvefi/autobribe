import boa
from contracts.markets import StakeDaoLogic
from eth_abi import encode


def test_constructor(stakedao_logic, crvusd, stakedao_market, manager):
    assert stakedao_logic.crvusd() == crvusd.address
    assert stakedao_logic.votemarket() == stakedao_market.address
    assert stakedao_logic.owner() == manager.address


def test_constructor_zeroaddr(crvusd, stakedao_market, manager):
    zero = boa.eval("empty(address)")

    with boa.reverts("zeroaddr: crvusd"):
        StakeDaoLogic(zero, stakedao_market, manager)
    with boa.reverts("zeroaddr: votemarket"):
        StakeDaoLogic(crvusd, zero, manager)
    with boa.reverts("zeroaddr: incentives_manager"):
        StakeDaoLogic(crvusd, stakedao_market, zero)


def test_create_bounty(stakedao_logic, stakedao_market, crvusd):
    stakedao_logic.internal.create_bounty(
        gauge := boa.env.generate_address(),
        400,
        1234
    )

    assert stakedao_market.creation_gauge() == gauge
    assert stakedao_market.creation_manager() == stakedao_logic.address
    assert stakedao_market.creation_rewardToken() == crvusd.address
    assert stakedao_market.creation_numberOfPeriods() == 2
    assert stakedao_market.creation_maxRewardPerVote() == 1234
    assert stakedao_market.creation_totalRewardAmount() == 400
    assert stakedao_market.eval("len(self.creation_blacklist)") == 0
    assert stakedao_market.creation_upgradeable() == True


def test_increase_bounty_duration(stakedao_logic, stakedao_market):
    random_id = 43958
    stakedao_logic.internal.increase_bounty_duration(
        random_id,
        400,
        1234)

    assert stakedao_market.increase_bountyId() == random_id
    assert stakedao_market.increase_additionalPeriods() == 2
    assert stakedao_market.increase_increasedAmount() == 400
    assert stakedao_market.increase_newMaxPricePerVote() == 1234


def test_bribe(stakedao_logic, stakedao_market, crvusd, manager):
    max_amount_per_vote = 12345
    encoded_max_amount_per_vote = encode(["uint256"], [max_amount_per_vote])

    random_gauge = boa.env.generate_address()
    random_id = 43958

    leftover_crvusd = 10 ** 18

    crvusd.mint_for_testing(stakedao_logic, leftover_crvusd)

    assert stakedao_logic.bounty_id(random_gauge) == 0

    with boa.env.prank(manager.address):
        stakedao_logic.bribe(
            random_gauge,
            400,
            bytes(encoded_max_amount_per_vote)
        )

    assert stakedao_logic.bounty_id(random_gauge) == 1234 # from mock

    stakedao_logic.eval(f"self.bounty_id[{random_gauge}] = {random_id}")

    assert stakedao_market.creation_gauge() == random_gauge
    assert stakedao_market.creation_manager() == stakedao_logic.address
    assert stakedao_market.creation_rewardToken() == crvusd.address
    assert stakedao_market.creation_numberOfPeriods() == 2
    assert (stakedao_market.creation_maxRewardPerVote() == max_amount_per_vote)
    assert stakedao_market.creation_totalRewardAmount() == 400
    assert stakedao_market.eval("len(self.creation_blacklist)") == 0
    assert stakedao_market.creation_upgradeable() == True

    # this part should be uninitialized after the first call
    assert stakedao_market.increase_bountyId() == 0
    assert stakedao_market.increase_additionalPeriods() == 0
    assert stakedao_market.increase_increasedAmount() == 0
    assert stakedao_market.increase_newMaxPricePerVote() == 0

    # cleaning dust
    assert crvusd.balanceOf(stakedao_logic.address) == 0
    assert crvusd.balanceOf(manager.address) == leftover_crvusd

    # we test for a second call because this time the bounty already exists
    increase_max_amount_per_vote = 54321
    increase_amount = 401
    encoded_increase_max_amount_per_vote= encode(["uint256"], [increase_max_amount_per_vote])
    crvusd.mint_for_testing(stakedao_logic, leftover_crvusd)

    with boa.env.prank(manager.address):
        stakedao_logic.bribe(
            random_gauge,
            increase_amount,
            bytes(encoded_increase_max_amount_per_vote)
        )

    assert stakedao_market.increase_bountyId() == random_id
    assert stakedao_market.increase_additionalPeriods() == 2
    assert stakedao_market.increase_increasedAmount() == increase_amount
    assert (stakedao_market.increase_newMaxPricePerVote() ==
            increase_max_amount_per_vote)

    # cleaning dust
    assert crvusd.balanceOf(stakedao_logic.address) == 0
    assert crvusd.balanceOf(manager.address) == leftover_crvusd * 2

    # this was manually overriden in the test through eval
    assert stakedao_logic.bounty_id(random_gauge) == random_id # from mock


def test_bribe_unauthorized(stakedao_logic):
    with boa.reverts("ownable: caller is not the owner"):
        stakedao_logic.bribe(boa.env.generate_address(), 400, bytes())

def test_close_bounty(stakedao_logic, stakedao_market, token_rescuer, crvusd):
    crvusd.mint_for_testing(stakedao_logic, 1000)
    with boa.env.prank(token_rescuer):
        stakedao_logic.close_bounty(7890, recovery_addr := boa.env.generate_address())
    assert crvusd.balanceOf(recovery_addr) == 1000
    assert stakedao_market.close_id() == 7890

def test_close_bounty_no_funds(stakedao_logic, stakedao_market, token_rescuer):
    with boa.env.prank(token_rescuer):
        with boa.reverts("manager: no unclaimed funds to recover"):
            stakedao_logic.close_bounty(7890, boa.env.generate_address())

def test_close_bounty_unauthorized(stakedao_logic):
    with boa.reverts("access_control: account is missing role"):
        stakedao_logic.close_bounty(7890, boa.env.generate_address())
