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
        "--no-cleanup",
        action="store_true",
        help="Does remove the extracted e.g. to see what went wrong",
    )

    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path where the patch should be applied or undone (default: None)",
    )
    args = parser.parse_args()

    base_path = (
        Path(get_install_location()) if args.base_path is None else Path(args.base_path)
    )
    data_path = base_path / "data"
    skills_pak = data_path / "skills/skills.pak"
    items_pak = data_path / "items/items.pak"
    eu_items_pak = data_path / "europe/Items/Items.pak"
    ui_pak =  base_path / "Textures" / "UI" / "UI.pak"

    skill_extact_folder = Path("./pak/skills").resolve()
    ui_extract_folder = Path("./pak/ui").resolve()
    items_extract_folder = Path("./pak/items").resolve()
    eu_items_folder = Path("./pak/eu_items").resolve()

    skill_extact_folder.mkdir(parents=True, exist_ok=True)
    items_extract_folder.mkdir(parents=True, exist_ok=True)
    eu_items_folder.mkdir(parents=True, exist_ok=True)
    ui_extract_folder.mkdir(parents=True, exist_ok=True)

    skill_pak_final = Path("./pak/skills.pak").resolve()
    items_pak_final = Path("./pak/items.pak").resolve()
    eu_items_pak_final = Path("./pak/eu_items.pak").resolve()
    ui_pak_final = Path("./pak/ui.pak").resolve()


    shutil.copyfile(skills_pak, skill_pak_final)
    if check_patched(items_pak, Path("./data/items/Items.pak")):
        if args.undo:
            shutil.copy(items_pak_final, items_pak)
    else:
        shutil.copyfile(items_pak, items_pak_final)

    if check_patched(eu_items_pak, Path("./data/europe/items/Items.pak")):
        if args.undo:
            shutil.copy(eu_items_pak_final, eu_items_pak)
    else:
        shutil.copyfile(eu_items_pak, eu_items_pak_final)


    if check_patched(ui_pak, Path("Textures/UI/UI.pak")):
        if args.undo:
            shutil.copy(ui_pak_final, ui_pak)
    else:
        shutil.copyfile(ui_pak, ui_pak_final)

    if args.undo:
        print("undoing patch")
        return

    pak = [
        (skill_pak_final, skill_extact_folder),
        (items_pak_final, items_extract_folder),
        (eu_items_pak_final, eu_items_folder),
    ]

    procs: list[Popen] = []

    print("extracting pak files")
    for file, folder in pak:
        file = str(file.resolve())
        folder = str(folder.resolve())

        procs.append(
            Popen(
                ["./pak2folder.exe", file, folder],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )

    procs.append(
        Popen(
            ["./pak2folder.exe", str(ui_pak_final.resolve()), str(ui_extract_folder.resolve()), "--xml-no-decode"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    )

    for proc in procs:
        proc.wait()

    print("Done extracting pak files")

    skill_tree = etree.parse("./pak/skills/client_skills.xml", None)
    root_skill = skill_tree.getroot()

    item_tree = etree.parse("./pak/items/client_items.xml", None)
    root_item = item_tree.getroot()

    item_tree_eu = etree.parse("./pak/eu_items/client_items.xml", None)
    root_item_eu = item_tree_eu.getroot()

    skill_map = {}

    skills = set()

    for s in root_skill:
        name = s.find("name")
        icon = s.find("skillicon_name")

        if name != None and icon != None:
            skill_map[name.text.lower()] = icon.text.removesuffix(".dds")

    mapping = {
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
        "187000050": "Wing_IDTiamat01a",
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
                if id in ["110601305", "111601272", "113601261", "114601261", "112601248"]:
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



            if args.rospet:
                if id in mapping:  # tiamat
                    mesh = mapping[id]
                    print(id, "changed to", mesh)
                    s.find("mesh").text = mesh

                    if(s.find("default_color_m") is not None):
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
            "./pak/eu_items/client_items.xml" if eu else "./pak/items/client_items.xml"
        )

        it.write(final_file_path, encoding="utf-8", xml_declaration=True)

    for skill_icon in skills:

        shutil.copyfile(
            Path("./pak/skills") / (skill_icon + ".dds"),
            Path("./pak/items") / (skill_icon + ".dds"),
        )

    Path("./data/items").mkdir(parents=True, exist_ok=True)
    Path("./data/europe/Items").mkdir(parents=True, exist_ok=True)
    Path("./Textures/UI").mkdir(parents=True, exist_ok=True)
    shutil.make_archive("./data/items/Items.pak", "zip", Path("./pak/items"))
    shutil.move("./data/items/Items.pak.zip", "./data/items/Items.pak")

    shutil.make_archive("./data/europe/Items/Items.pak", "zip", Path("./pak/eu_items"))
    shutil.move("./data/europe/Items/Items.pak.zip", "./data/europe/items/Items.pak")
    if args.ui:
        shutil.copy("v3_common_01.dds", "./pak/ui/v3_common_01.dds")
        shutil.make_archive("./Textures/UI/UI.pak", "zip", Path("./pak/ui"))
        shutil.move("./Textures/UI/UI.pak.zip", "./Textures/UI/UI.pak")


    if not args.no_cleanup:
        for folder in [skill_extact_folder, items_extract_folder, eu_items_folder, ui_extract_folder]:
            shutil.rmtree(folder, True)


    if args.wings or args.sw:
        shutil.copytree("./objects", base_path/"objects", dirs_exist_ok=True)

    print("overwriting files")
    shutil.copy("./data/items/Items.pak", items_pak)
    shutil.copy("./data/europe/items/Items.pak", eu_items_pak)
    shutil.copy("./Textures/UI/UI.pak", ui_pak)

    print("done")


from glob import glob

if __name__ == "__main__":
    main()
