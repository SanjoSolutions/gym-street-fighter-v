from enum import IntEnum


class MoveEmbedding(IntEnum):
    LP = 2304
    MP = 2560
    HP = 3072
    LK = 4352
    MK = 4608
    HK = 5120
    CollarboneBreaker = 2562
    SolarPlexusStrike = 3074
    AxeKick = 5122
    ShoulderThrow = 8192
    SomersaultThrow = 2105344
    MindsEye = 32
    DenjinRenki = 128
    Hashogeki = 64
    VShift = 2147483648
    LHadoken = 16644
    MHadoken = 16900
    HHadoken = 17412
    ExHadoken = 16392
    LShoryuken = 260
    MShoryuken = 516
    HShoryuken = 1028
    ExShoryuken = 8
    ShinkuHadoken = 272
    ShinkuHadoken2 = 528
    ShinkuHadoken3 = 1040
    Unknown1 = -2147483648  # shift?
    Unknown2 = 1
    Unknown3 = -1046599492


move_to_index = dict((move, index) for index, move in enumerate(MoveEmbedding))


def move_to_embedding(move):
    index = move_to_index[move]
    return generate_move_embedding(index)


def generate_move_embedding(move_index):
    embedding = [0] * len(MoveEmbedding)
    embedding[move_index] = 1
    return tuple(embedding)
