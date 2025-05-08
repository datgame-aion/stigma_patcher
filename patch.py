# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "lxml",
# ]
# ///

import argparse
from lxml import etree
from pathlib import Path
import shutil
import hashlib
from subprocess import Popen
import subprocess
import winreg

BIG_UI = [
    '<Skin name="v3_hud_target_normal_start" texture="textures/ui/v3_hud_01" src_image="4,495,100,84"></Skin>',
    '<Skin name="v3_hud_target_elite_start" texture="textures/ui/v3_hud_01" src_image="4,409,100,84"></Skin>',
    '<Skin name="v3_hud_target_elite_start" texture="textures/ui/v3_hud_01" src_image="4,409,100,84"></Skin>',
    '<Skin name="v3_hud_target_hero_mod" src_image="104,324,381,84" texture="textures/ui/v3_hud_01"></Skin>',
]


def get_install_location():
    try:
        key_path = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{cdc124e6-6e04-4867-a651-135e589f8fd1}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
        return install_location
    except FileNotFoundError:
        return None


def check_patched(f1: Path, f2: Path):
    if not (f1.exists()) or not (f2.exists()):
        return False
    with open(f1, "rb") as f1, open(f2, "rb") as f2:
        return (
            hashlib.file_digest(f1, "sha256").hexdigest()
            == hashlib.file_digest(f2, "sha256").hexdigest()
        )


from typing import Optional


class MyArgs(argparse.Namespace):
    undo: bool
    agent: bool
    wings: bool
    white: bool
    ui: bool
    rospet: bool
    cammi: bool
    madnez: bool
    no_cleanup: bool
    base_path: Optional[str]
    ui_big: bool
    lang: Optional[str]
    lucky: bool
    no_stigma: bool
    no_cloud: bool


from dataclasses import dataclass, field


@dataclass
class PakFile:
    game_loc: str
    cache_loc: str
    extract_loc: str
    patched_loc: Optional[str]
    required: bool
    args: list[str] = field(default_factory=lambda: [])

    def cp(self, undo: bool):
        Path(self.extract_loc).mkdir(parents=True, exist_ok=True)
        if self.patched_loc is not None:
            Path(self.patched_loc).parent.mkdir(parents=True, exist_ok=True)

            if check_patched(Path(self.game_loc), Path(self.patched_loc)):
                shutil.copy(self.cache_loc, self.game_loc)
                if undo:
                    return

        shutil.copyfile(self.game_loc, self.cache_loc)

    def extract(self):
        if not self.required:
            return
        return Popen(
            [
                "./pak2folder.exe",
                str(Path(self.cache_loc).resolve()),
                str(Path(self.extract_loc).resolve()),
            ]
            + self.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def get_extract(self):
        return Path(self.extract_loc).resolve()

    def make_zip(self, patch: bool):
        if not self.required:
            return
        shutil.make_archive(Path(self.patched_loc), "zip", self.extract_loc)
        shutil.move(self.patched_loc + ".zip", Path(self.patched_loc))

        if patch:
            shutil.copy(self.patched_loc, self.game_loc)


def main() -> None:

    parser = argparse.ArgumentParser(
        description="A script to apply and optionally undo the Stigma patch to aion classic eu\n"
        "(and potentionally other classic servers if given their path with --base-path)"
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the applied patch instead of applying it",
    )

    parser.add_argument(
        "--agent",
        action="store_true",
        help="Applies the Agent GS extend skin onto lannok",
    )

    parser.add_argument(
        "--wings",
        action="store_true",
        help="Applies the Phaistos wings onto Romantic wings",
    )

    parser.add_argument(
        "--white",
        action="store_true",
        help="Makes cavalier plate armor white",
    )

    parser.add_argument(
        "--ui",
        action="store_true",
        help="Simplifies the style of the UI",
    )

    parser.add_argument(
        "--rospet",
        action="store_true",
        help="Adds (new) changes rospet wants",
    )

    parser.add_argument(
        "--cammi",
        action="store_true",
        help="Adds (new) changes cammi wants",
    )

    parser.add_argument(
        "--no-cloud",
        action="store_true",
        help="Removes clouds on Eos map",
    )

    parser.add_argument(
        "--madnez",
        action="store_true",
        help="Adds changes madnez wants",
    )

    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Does remove the extracted e.g. to see what went wrong",
    )

    parser.add_argument(
        "--no-stigma",
        action="store_true",
        help="Does not patch stigma",
    )

    parser.add_argument(
        "--lucky",
        action="store_true",
        help="makes you lucky in solo crucible",
    )

    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path where the patch should be applied or undone (default: None)",
    )

    parser.add_argument(
        "--ui-big",
        action="store_true",
        help="Makes all target bars in the ui the same size",
    )

    parser.add_argument(
        "--lang",
        type=str,
        default="ENG",
        help="Chooses the language to patched if l10n is patched set by default to eng",
    )

    args = parser.parse_args(namespace=MyArgs())

    base_path = (
        Path(get_install_location()) if args.base_path is None else Path(args.base_path)
    )
    data_path = base_path / "data"

    f_skill_pak = PakFile(
        data_path / "skills/skills.pak",
        "./pak/skills.pak",
        "./pak/skills",
        None,
        required=True,
    )

    f_item_pak = PakFile(
        data_path / "items/items.pak",
        "./pak/items.pak",
        "./pak/items",
        "./patched/data/items/Items.pak",
        required=not args.no_stigma
        or args.agent
        or args.wings
        or args.white
        or args.rospet
        or args.madnez,
    )
    f_eu_item_pak = PakFile(
        data_path / "europe/Items/Items.pak",
        "./pak/eu_items.pak",
        "./pak/eu_items",
        "./patched/data/europe/items/Items.pak",
        required=not args.no_stigma
        or args.agent
        or args.wings
        or args.white
        or args.rospet
        or args.madnez,
    )
    f_ui_pak = PakFile(
        base_path / "Textures" / "UI" / "UI.pak",
        "./pak/ui.pak",
        "./pak/ui",
        "./patched/Textures/UI/UI.pak",
        required=args.ui | args.ui_big | args.cammi,
        args=["--xml-no-decode"],
    )
    f_eu_npc_pak = PakFile(
        base_path / "data" / "europe" / "npcs" / "npcs.pak",
        "./pak/npcs.pak",
        "./pak/npcs",
        "./patched/data/europe/npcs/npcs.pak",
        required=args.lucky,
        args=["--utf16"],
    )
    f_npc_pak = PakFile(
        base_path / "data" / "npcs" / "npcs.pak",
        "./pak/eu_npcs.pak",
        "./pak/eu_npcs",
        "./patched/data/npcs/npcs.pak",
        required=args.lucky,
        args=["--utf16"],
    )
    f_l10n_pak = PakFile(
        base_path / "l10n" / args.lang / "Data" / "Data.pak",
        "./pak/l10n.pak",
        "./pak/l10n",
        f"./patched/l10n/{args.lang}/Data/Data.pak",
        required=args.ui | args.ui_big | args.cammi,
        args=["--utf16"],
    )

    paks = [
        f_skill_pak,
        f_item_pak,
        f_eu_item_pak,
        f_ui_pak,
        f_eu_npc_pak,
        f_npc_pak,
        f_l10n_pak,
    ]

    procs: list[Optional[Popen]] = []

    if not args.undo:
        print("extracting pak files")

    no_cloud_final = base_path / "Effects" / "Effects_Textures2.pak"
    if (no_cloud_final).exists():
        no_cloud_final.unlink()

    for pak in paks:
        pak.cp(args.undo)
        if not args.undo:
            procs.append(pak.extract())

    if args.undo:
        print("undoing patch")
        return

    for proc in procs:
        if proc is not None:
            proc.wait()

    print("Done extracting pak files")

    skill_map = {}

    skills = set()

    patch_stigma = not args.no_stigma

    if (
        patch_stigma
        or args.agent
        or args.wings
        or args.white
        or args.rospet
        or args.madnez
    ):

        skill_tree = etree.parse(f_skill_pak.get_extract() / "client_skills.xml", None)
        root_skill = skill_tree.getroot()

        item_tree = etree.parse(f_item_pak.get_extract() / "client_items.xml", None)
        root_item = item_tree.getroot()

        item_tree_eu = etree.parse(
            f_eu_item_pak.get_extract() / "client_items.xml", None
        )
        root_item_eu = item_tree_eu.getroot()
        for s in root_skill:
            name = s.find("name")
            icon = s.find("skillicon_name")

            if name != None and icon != None:
                if patch_stigma:
                    skill_map[name.text.lower()] = icon.text.removesuffix(".dds")

        mapping = {
            # pvp
            "110601343": "PL_IDTiamat01a_body",  #     Chest     to 110601317
            "113601298": "PL_IDTiamat01a_leg",  #      Pants     to 113601271
            "114601298": "PL_IDTiamat01a_foot",  #     Boots     to 114601266
            "111601309": "PL_IDTiamat01a_hand",  #     Gloves    to 111601282
            "112601285": "CH_IDTiamat01a_shoulder",  # Shoulders to 112501244
            # sw
            "110600968": "PL_IDTiamat01a_body",  #     Chest     to 110601317
            "113600931": "PL_IDTiamat01a_leg",  #      Pants     to 113601271
            "114600926": "PL_IDTiamat01a_foot",  #     Boots     to 114601266
            "111600947": "PL_IDTiamat01a_hand",  #     Gloves    to 111601282
            "112600922": "CH_IDTiamat01a_shoulder",  # Shoulders to 112501244
            # supply
            "110601284": "PL_IDTiamat01a_body",  #     Chest     to 110601317
            "113601240": "PL_IDTiamat01a_leg",  #      Pants     to 113601271
            "114601240": "PL_IDTiamat01a_foot",  #     Boots     to 114601266
            "111601249": "PL_IDTiamat01a_hand",  #     Gloves    to 111601282
            "112601227": "CH_IDTiamat01a_shoulder",  # Shoulders to 112501244
            # rest
            "187000058": "Wing_IDTiamat01a",
            "100000893": "SW_Cash_Ninja01",
            "115000966": "SH_cash_buckler02",
        }

        for ffff in ["eu", "normal"]:
            eu = ffff == "eu"
            rr = root_item_eu if eu else root_item
            for s in rr:
                name = s.find("name")
                id = s.find("id").text.lower()
                icon = s.find("icon_name")
                gain_skill1 = s.find("gain_skill1")

                # rospet armor to white
                if args.white:
                    if id in [
                        "110601305",
                        "111601272",
                        "113601261",
                        "114601261",
                        "112601248",
                    ]:
                        print("changed armor to white")
                        s.find("default_color_m").text = "255,255,255"
                        s.find("default_color_f").text = "255,255,255"

                if args.agent:
                    if id in [
                        "100900571",
                    ]:  # rospet lannok to agent extend
                        s.find("mesh").text = "TS_U011"

                if args.wings:
                    if id in [
                        "187050017",
                    ]:  # test Romantic Wings to beritra
                        s.find("mesh").text = "Wing_IDVritra02a"

                if args.madnez:
                    if id in [
                        "100900570",
                    ]:  # trioran gs to https://aioncodex.com/5x/item/100901098/
                        s.find("mesh").text = "TS_U011"

                    if id in [
                        "100901109",
                    ]:  # some gs to https://aioncodex.com/5x/item/100900934/
                        s.find("mesh").text = "TS_D04a"

                if args.wings:
                    if id in [
                        "110101435",
                    ]:  # test cav chest to new skins
                        pass
                        # s.find("mesh").text = "CH_GhostWarrior01_body"
                        # s.find("default_color_m").text = "77,0,0"
                        # s.find("default_color_f").text = "77,0,0"

                if args.rospet:
                    if id in mapping:  # tiamat
                        mesh = mapping[id]
                        print(id, "changed to", mesh)
                        s.find("mesh").text = mesh

                        if s.find("default_color_m") is not None:
                            s.find("default_color_m").text = "255,255,255"
                            s.find("default_color_f").text = "255,255,255"

                        if id == "115000966":
                            s.find("default_color_m").text = "76,147,225"
                            s.find("default_color_f").text = "76,147,225"

                if name != None and icon != None and gain_skill1 != None:
                    name = name.text.lower()
                    gain_skill1 = gain_skill1.text.lower()

                    new_icon = skill_map.get(gain_skill1)
                    if new_icon != None:
                        icon.text = new_icon
                        skills.add(new_icon)

            it = item_tree_eu if eu else item_tree

            final_file_path = (
                f_eu_item_pak.get_extract() / "client_items.xml"
                if eu
                else f_item_pak.get_extract() / "client_items.xml"
            )

            it.write(final_file_path, encoding="utf-8", xml_declaration=True)

        for skill_icon in skills:

            shutil.copyfile(
                Path("./pak/skills") / (skill_icon + ".dds"),
                Path("./pak/items") / (skill_icon + ".dds"),
            )

    if args.lucky:
        for f in [
            f_npc_pak.get_extract() / "client_npcs.xml",
            f_eu_npc_pak.get_extract() / "client_npcs.xml",
        ]:
            npc_tree = etree.parse(f, None)
            root_npc = npc_tree.getroot()
            for s in root_npc:
                id = s.find("id").text.lower()

                if id in ["217829", "217832", "217835"]:
                    s.find("scale").text = "400"

            npc_tree.write(f, encoding="utf-8", xml_declaration=True)

    if args.ui_big:
        fi = "./pak/l10n/ui/preload/hud_s2.xml"
        l10n_tree = etree.parse(fi, None)
        l10n_root = l10n_tree.getroot()
        target_skin = l10n_root.xpath('//Skin[@name="v3_hud_target_legend"]')[0]
        for skin_str in BIG_UI:  # reversed to preserve order
            new_skin = etree.fromstring(skin_str)
            target_skin.addnext(new_skin)
        l10n_tree.write(fi, encoding="utf-8", xml_declaration=True)

        shutil.copy(
            "target_dialog.xml",
            Path(f_l10n_pak.extract_loc) / "ui" / "game" / "target_dialog.xml",
        )

    if args.cammi:
        shutil.copy(
            "basic_status_dialog_cammi.xml",
            Path(f_l10n_pak.extract_loc)
            / "ui"
            / "game_hud_s2"
            / "basic_status_dialog_cammi.xml",
        )

    if not args.no_stigma:
        f_item_pak.make_zip(True)
        f_eu_item_pak.make_zip(True)

    if args.ui_big or args.cammi:
        f_l10n_pak.make_zip(True)

    if args.lucky:
        f_npc_pak.make_zip(True)
        f_eu_npc_pak.make_zip(True)

    if args.ui:
        shutil.copy("v3_common_01.dds", "./pak/ui/v3_common_01.dds")

    if args.ui_big:
        shutil.copy("v3_hud_01.dds", "./pak/ui/v3_hud_01.dds")

    if args.cammi:
        shutil.copy("v3_hud_01_cammi.dds", "./pak/ui/v3_hud_01.dds")

    if args.ui or args.ui_big:
        f_ui_pak.make_zip(True)

    if not args.no_cleanup:
        for folder in paks:
            shutil.rmtree(folder.extract_loc, True)

    if args.wings or args.rospet or args.madnez:
        shutil.copytree("./objects", base_path / "objects", dirs_exist_ok=True)

    if args.no_cloud:
        shutil.copy("ihateclouds.pak", no_cloud_final)

    print("overwriting files")

    print("done")


if __name__ == "__main__":
    main()
