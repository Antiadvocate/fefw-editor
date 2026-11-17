"""Keep the Flags page and generated name dictionary on the same catalogues."""
import audiences
import boons
import deeds
import fast_travel
import facilities
import facility_access
import fefw_core as core
import tutorials
import unit_entries

KNOWN_FLAGS = {
    0xb9a0e16b: ('禁止_武器屋', 'Disabled: Armorer'),
    0x5e9748e0: ('禁止_道具屋', 'Disabled: Item shop'),
    0x3fdd2f30: ('神殿_転移_カーラ神殿', 'Registered: Gate of the Gods: Kalla'),
    0x63fc6b22: ('機能開放_厩舎', 'Facility unlocked: Stables'),
}


def apply_labels(names: dict[int, dict], *, strict: bool = True) -> None:
    for h, (key, label) in KNOWN_FLAGS.items():
        if core.id_hash(key) != h or names.get(h, {}).get('name', key) != key:
            if strict:
                raise core.SaveError(f'Conflicting known flag identity for {h:08x}')
            continue
        names[h] = {**names.get(h, {}), 'name': key, 'label': label}
    for module in (tutorials, fast_travel, audiences, deeds, boons, facilities, facility_access, unit_entries):
        # A bad catalogue must not leave a partial overlay behind. The Flags
        # page can still display raw records; catalogue pages report errors.
        updated = dict(names)
        try:
            module.apply_labels(updated)
        except core.SaveError:
            if strict:
                raise
        else:
            names.update(updated)
