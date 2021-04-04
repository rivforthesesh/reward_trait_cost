# for config file (used for settings)
import configparser
import os
from pathlib import Path
# for commands
import sims4.commands
# from whims.whims_tracker
import whims.whims_tracker
from protocolbuffers import Sims_pb2
from protocolbuffers.DistributorOps_pb2 import Operation, SetWhimBucks
from distributor.ops import GenericProtocolBufferOp
from distributor.system import Distributor
import services, sims4.log, sims4.random
logger = sims4.log.Logger('Whims', default_owner='jjacobson')

# sort out cfg
config_dir = Path(__file__).resolve().parent.parent
config_name = 'riv_reward_trait_cost.cfg'
config_path = os.path.join(config_dir, config_name)
config = configparser.ConfigParser()
header = 'your settings (new_cost = ceil(multiplier * cost) + addend)'

# set up cfg
if not os.path.isfile(config_path):
    config[header] = {}
    config[header]['multiplier'] = '1'
    config[header]['addend'] = '0'
    # write cfg
    with open(config_path, 'w') as cfg_file:
        config.write(cfg_file)

# read from cfg
config.read_file(open(config_path, 'r'))
multiplier = float(config.get(header, 'multiplier'))
addend = int(config.get(header, 'addend'))


# floor function without math
def floor(x: float):
    y = round(x)
    if y > x:
        return y-1
    else:
        return y


# ceil function without math
def ceil(x: float):
    y = round(x)
    if y < x:
        return y+1
    else:
        return y


def riv_purchase_whim_award(self, reward_guid64):
    reward_instance = services.get_instance_manager(sims4.resources.Types.REWARD).get(reward_guid64)
    award = reward_instance

    cost = ceil(self.SATISFACTION_STORE_ITEMS[reward_instance].cost * multiplier) + addend

    if self._sim_info.get_whim_bucks() < cost:
        logger.debug('Attempting to purchase a whim award with insufficient funds: Cost: {}, Funds: {}', cost,
                     self._sim_info.get_whim_bucks())
        return
    self._sim_info.add_whim_bucks((-cost), (SetWhimBucks.PURCHASED_REWARD), source=reward_guid64)
    award.give_reward(self._sim_info)


def riv_send_satisfaction_reward_list(self):
    msg = Sims_pb2.SatisfactionRewards()
    for reward, data in self.SATISFACTION_STORE_ITEMS.items():
        reward_msg = Sims_pb2.SatisfactionReward()
        reward_msg.reward_id = reward.guid64
        reward_msg.cost = ceil(data.cost * multiplier) + addend
        reward_msg.affordable = True if reward_msg.cost <= self._sim_info.get_whim_bucks() else False
        reward_msg.available = reward.is_valid(self._sim_info)
        reward_msg.type = data.award_type
        unavailable_tooltip = reward.get_unavailable_tooltip(self._sim_info)
        if unavailable_tooltip is not None:
            reward_msg.unavailable_tooltip = unavailable_tooltip
        msg.rewards.append(reward_msg)

    msg.sim_id = self._sim_info.id
    distributor = Distributor.instance()
    distributor.add_op_with_no_owner(GenericProtocolBufferOp(Operation.SIM_SATISFACTION_REWARDS, msg))


# replace originals
whims.whims_tracker.WhimsTracker.purchase_whim_award = riv_purchase_whim_award
whims.whims_tracker.WhimsTracker.send_satisfaction_reward_list = riv_send_satisfaction_reward_list


def are_m_and_a_valid(m: float, a: int, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        if m == 0:
            if a >= 0:
                output('all of your reward traits now cost ' + str(a) + ' points')
            else:
                output('all of your reward traits now cost less than 0. changing to default settings...')
                console_set_m(1, True, _connection)
                console_set_a(0, _connection)
        else:
            min_cost = 0
            # get min cost
            if a < 0:
                while ceil(min_cost * m) + a < 0:
                    # we enter this while loop if a 0-point reward will become negative
                    # can increment min_cost as m is positive
                    min_cost += 1
            if min_cost > 0:
                min_cost -= 1
                output('please note that the rewards store won\'t work properly if you have any reward traits with '
                       'an original cost of ' + str(min_cost) + ' or less, as the new cost will be negative.')
    except Exception as e:
        output('something went wrong with checking if your settings are valid: ' + str(e))
        output('please let me (rivforthesesh / riv#4381) know on itch.io or discord!')


# set multiplier
# called_by_other ensures that the 'are_m_and_a_valid' function does not run twice
@sims4.commands.Command('riv_reward_trait_cost_multiplier', command_type=sims4.commands.CommandType.Live)
def console_set_m(m: float, called_by_other=False, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # set new reward multiplier
        global multiplier
        multiplier = abs(m)
        # write to cfg
        config[header]['multiplier'] = str(abs(m))
        with open(config_path, 'w') as cfg_file:
            config.write(cfg_file)
        # it went well yay
        output('set your reward trait cost multiplier to ' + str(abs(m)))
        a = addend
        if not called_by_other:
            are_m_and_a_valid(m, a, _connection)
    except Exception as e:
        output('something went wrong with riv_reward_trait_cost_set_multiplier: ' + str(e))
        output('please let me (rivforthesesh / riv#4381) know on itch.io or discord!')
        
        
# set addend
@sims4.commands.Command('riv_reward_trait_cost_addend', command_type=sims4.commands.CommandType.Live)
def console_set_a(a: int, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # set new reward addend
        global addend
        addend = a
        # write to cfg
        config[header]['addend'] = str(a)
        with open(config_path, 'w') as cfg_file:
            config.write(cfg_file)
        # it went well yay
        output('set your reward trait cost addend to ' + str(a))
        m = multiplier
        are_m_and_a_valid(m, a, _connection)
    except Exception as e:
        output('something went wrong with riv_reward_trait_cost_set_addend: ' + str(e))
        output('please let me (rivforthesesh / riv#4381) know on itch.io or discord!')


# set both
@sims4.commands.Command('riv_reward_trait_cost_set', command_type=sims4.commands.CommandType.Live)
def console_set(m: float, a: int, _connection=None):
    console_set_m(m, True, _connection)
    console_set_a(a, _connection)


# reload cfg
@sims4.commands.Command('riv_reward_trait_cost_config', command_type=sims4.commands.CommandType.Live)
def console_reload_cfg(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # read from cfg
        config.read_file(open(config_path, 'r'))
        # pull from file
        m = abs(float(config.get(header, 'multiplier')))
        a = int(config.get(header, 'addend'))
        output('reloaded riv_reward_trait_cost.cfg - your new settings will now be applied to the reward traits store')
        console_set(m, a, _connection)
    except Exception as e:
        output('something went wrong with riv_reward_trait_cost_config: ' + str(e))
        output('please let me (rivforthesesh / riv#4381) know on itch.io or discord!')
