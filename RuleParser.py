import re
import csv
import json
from typing import Dict, NamedTuple, List, Optional


def multiple_replace(string: str, rep_dict: Dict[str, str]) -> str:
    pattern = re.compile(
        "|".join([re.escape(k) for k in sorted(rep_dict, key=len, reverse=True)]),
        flags=re.DOTALL,
    )
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)


def parse_subsection(rule: str) -> str:
    raw_translations = {
        "FireWand": "Fire Wand",
        "Feather": "Penguin's Feather",
        "Dark Sword": "Dark Sword",
        "Red": "Red Key",
        "Light": "Light",
        "Green": "Green Key",
        "Fire": "Fire",
        "Conch": "Conch",
        "Blue": "Blue Key",
        "Purple": "Purple Key",
        "Wand": "Wand",
        "Ghost Spear": "Ghost Spear",
        "Yellow": "Yellow Key",
        "Health": "Health",
        "Dark Shield": "Dark Shield",
        "Dark Suit": "Dark Suit",
        "Ghost Sword": "Ghost Sword",
        "Sword": "Sword",
        "Shield": "Shield",
        "Spear": "Ghost Spear",
        "Shards": "Shards"
    }
    translations = {
        old: f'has_item(state, player, "{new}")' for old, new in raw_translations.items()
    }
    rule = multiple_replace(rule, translations)
    rule = multiple_replace(rule, {"\n": ""})
    rule = rule.replace("/", "or")
    rule = rule.replace("&", "and")
    return rule


def parse_rule(location_name: str, rule: str) -> str:
    sections = []
    standard_match = re.search("\[Standard:([^\[]*)]", rule)
    if standard_match:
        text = parse_subsection(standard_match.group(1))
        sections.append(text)
    tricky_match = re.search("\[Tricky:([^\[]*)]", rule)
    if tricky_match:
        text = parse_subsection(tricky_match.group(1))
        sections.append(
            f"(state.multiworld.difficulty[player].value >= Difficulty.option_tricky) and ({text})"
        )
    unreasonable_match = re.search("\[Unreasonable:([^\[]*)]", rule)
    if unreasonable_match:
        text = parse_subsection(unreasonable_match.group(1))
        sections.append(
            f"(state.multiworld.difficulty[player].value >= Difficulty.option_unreasonable) and ({text})"
        )
    if len(sections) == 0:
        return ""
    combined_rules = " or ".join(map(lambda x: f"({x})", sections))
    return f'multiworld.get_location("{location_name}", player).access_rule = lambda state: ({combined_rules})'


class RawSeedlingLocation(NamedTuple):
    display_name: str
    region: str
    flash_name: str
    is_boss: str
    ID: str
    rule: str


class RawSeedlingItem(NamedTuple):
    display_name: str
    flash_name: str
    ID: str
    type: str


def locations_to_rules(locations: List[RawSeedlingLocation]) -> str:
    #WARNING: Doesn't include boss rules!
    results = []
    for loc in locations:
        results.append(parse_rule(loc.display_name, loc.rule))
    return "\n    ".join(results)


def locations_to_py(locations: List[RawSeedlingLocation]) -> str:
    location_list = map(
        lambda loc: f"\"{loc.display_name}\": SeedlingLocationData(region=\"{loc.region}\", address={loc.ID} + offset, is_boss={loc.is_boss == 'Yes'})",
        locations,
    )
    return "{" + ", ".join(location_list) + "}"


def items_to_py(items: List[RawSeedlingItem]) -> str:
    item_list = map(
        lambda item: f'"{item.display_name}": SeedlingItemData(code={item.ID} + offset, type=ItemClassification.{item.type})',
        items,
    )
    return "{" + ", ".join(item_list) + "}"


def locations_to_js(locations: List[RawSeedlingLocation]) -> str:
    location_list = map(
        lambda loc: {
            "display_name": loc.display_name,
            "flash_name": loc.flash_name,
            "ID": loc.ID,
            "is_boss": loc.is_boss == "Yes",
        },
        locations,
    )
    return json.dumps(list(location_list))


def items_to_js(items: List[RawSeedlingLocation]) -> str:
    item_list = map(
        lambda item: {
            "display_name": item.display_name,
            "flash_name": item.flash_name,
            "ID": item.ID,
        },
        items,
    )
    return json.dumps(list(item_list))


def csv_to_locations(filename: str) -> List[RawSeedlingLocation]:
    results = []
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for line in reader:
            results.append(
                RawSeedlingLocation(
                    display_name=line["display_name"],
                    region=line["region"],
                    flash_name=line["flash_name"],
                    is_boss=line["is_boss"],
                    ID=line["ID"],
                    rule=line["rule"],
                )
            )
    return results


def csv_to_items(filename: str) -> List[RawSeedlingItem]:
    results = []
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for line in reader:
            results.append(
                RawSeedlingItem(
                    display_name=line["display_name"],
                    flash_name=line["flash_name"],
                    ID=line["ID"],
                    type=line["type"],
                )
            )
    return results
