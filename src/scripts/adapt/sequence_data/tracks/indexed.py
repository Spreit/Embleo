from copy import deepcopy


def put_clip(clips, index, values):
    """Native masters address slots by serialized index, not shot occurrence."""
    if type(index) is not int or not 0 <= index < 4096:
        raise ValueError(f'Invalid sequence clip index: {index}')
    slot = clips.setdefault(index, {})
    for key, value in values.items():
        # Repeated timeline shots can share a slot; native AddClipData keeps
        # its first payload while allowing other clip families at that index.
        slot.setdefault(key, deepcopy(value))


def indexed_data(clips):
    return [clips.get(i, {}) for i in range(max(clips, default=-1) + 1)]
