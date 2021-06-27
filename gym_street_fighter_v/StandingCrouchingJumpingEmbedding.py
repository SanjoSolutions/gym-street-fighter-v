from enum import IntEnum


class StandingCrouchingJumpingEmbedding(IntEnum):
    Standing = 1
    Crouching = 2
    Unknown1 = 3
    Jumping = 4
    Unknown3 = 9
    Unknown2 = 11


standing_crouching_jumping_to_index = dict(
    (standing_crouching_jumping, index)
    for index, standing_crouching_jumping
    in enumerate(StandingCrouchingJumpingEmbedding)
)


def standing_crouching_jumping_to_embedding(standing_crouching_jumping):
    index = standing_crouching_jumping_to_index[standing_crouching_jumping]
    return generate_standing_crouching_jumping_embedding(index)


def generate_standing_crouching_jumping_embedding(standing_crouching_jumping_index):
    embedding = [0] * len(StandingCrouchingJumpingEmbedding)
    embedding[standing_crouching_jumping_index] = 1
    return tuple(embedding)
