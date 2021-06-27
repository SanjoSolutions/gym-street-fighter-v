from gym.envs.registration import register

register(
    id='street-fighter-v-v4',
    entry_point='gym_street_fighter_v.envs:StreetFighterVEnv',
)
