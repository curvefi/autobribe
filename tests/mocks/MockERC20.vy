# pragma version ~=0.4.0

from snekmate.tokens import erc20
from snekmate.auth import ownable

initializes: ownable
initializes: erc20[ownable := ownable]

exports: erc20.__interface__


@deploy
def __init__():
    ownable.__init__()
    erc20.__init__("mock", "mock", 18, "mock", "mock")
