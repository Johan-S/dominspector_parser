import xml.etree.ElementTree as ET
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import os
import shutil
import nations.ma as ma
import nations.la as la
import nations.ea as ea
from typing import NamedTuple



chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1024x1400")

# download Chrome Webdriver
# https://sites.google.com/a/chromium.org/chromedriver/download
# put driver executable file in the script directory
chrome_driver = os.path.join(os.getcwd(), "chromedriver")

driver = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver)
driver.implicitly_wait(30)

url = "https://larzm42.github.io/dom5inspector/?page=unit&nation=7&unittype=1&unitnat=1&showids=1"

driver.get(url)

driver.find_element_by_css_selector(".r0")
unitnat = driver.find_element_by_css_selector("#unitnat")
unittype = Select(driver.find_element_by_css_selector("#unittype"))
nation_select = Select(driver.find_element_by_css_selector(".filters-nation .nation"))



class Unit(NamedTuple):
  id: int
  name: str
  type: str
  base_name: str
  gold: str
  resources: str


def Refresh():
  unitnat.click()
  time.sleep(0.1)
  unitnat.click()
  time.sleep(0.1)


def ExtractUnits():
  units = []
  names = set()
  for unit_row in driver.find_elements_by_css_selector(".slick-row"):
    id = unit_row.find_element_by_css_selector(".r0").text
    name = unit_row.find_element_by_css_selector(".r1").text
    t = unit_row.find_element_by_css_selector(".r3").text
    gold = unit_row.find_element_by_css_selector(".r4").text
    resources = unit_row.find_element_by_css_selector(".r5").text
    bn = name.lower().replace(' ', '_')
    on = bn
    i = 1
    while bn in names:
      i += 1
      bn = on + '_%d' % i
    names.add(bn)
    units.append(Unit(id, name, t, bn, gold, resources))
  units.sort(key=lambda x: x.type + '%04s' % x.gold + x.name)
  return units


def GetUnits(nat_id):
  nation_select.select_by_value(nat_id)
  unittype.select_by_index(2)
  Refresh()
  return ExtractUnits()


def GetSummons(nat_id):
  nation_select.select_by_value(nat_id)
  unittype.select_by_index(6)
  Refresh()
  return ExtractUnits()


def GetoHeroes(nat_id):
  nation_select.select_by_value(nat_id)
  unittype.select_by_index(9)
  Refresh()
  return ExtractUnits()


def GetPretenders(nat_id):
  nation_select.select_by_value(nat_id)
  unittype.select_by_index(8)
  Refresh()
  return ExtractUnits()


def PrintNationUnits(nat_id):
  for a in GetUnits(nat_id): print(a)
  for a in GetoHeroes(nat_id): print(a)
  for a in GetPretenders(nat_id): print(a)


def FixNames(unit_list):
  us = {}
  for u in unit_list:
    name = u.base_name
    o_name = name
    i = 1
    while name in us:
      i += 1
      name = o_name + '_%d' % i



def images_to_export(nation_id, to_dir):
  us = {}
  for u in GetUnits(nation_id) + GetSummons(nation_id) + GetoHeroes(nation_id):
    us[u.base_name] = u.id
  files = []
  for k, v in us.items():
      orig = "data/images/sprites/%04d_1.png" % int(v)
      files.append((orig, os.path.join(to_dir, k + '.png')))
  return files


def MakeNationImageFolder(nation_id, folder):
    os.mkdir(folder)
    imgs = images_to_export(nation_id, folder)
    for src, dst in imgs:
        shutil.copy(src, dst)


def PublicAttr(mod):
  return [a for a in dir(mod) if not a.startswith('_')]


def MakeAllNationImageFolders(mod):
  mn = mod.__name__
  for n in PublicAttr(mod):
    MakeNationImageFolder(getattr(ma, n), "nations/%s_%s" % (mn, n))


unit_table_header = """^ Sprite  ^ Unit Name  ^ Magic    ^ Type  ^ Comments  ^"""

unit_row_pattern = """| %s    | **%s**\\ {{:misc:gui:gold.png?15&nolink}} %s\\ {{:misc:gui:resources.png?15&nolink}} %s   |  | %s  |  Manual description here.  |"""
summon_row_pattern = """| %s    | **%s**  |  | %s  |  Manual description here.  |"""

def MakeUnitRow(u: Unit, era:str, nation):
  img = "{{:nations:%s:%s:%s.png?30&nolink}}" % (era, nation, u.base_name)
  if u.resources:
    return unit_row_pattern % (img, u.name, u.gold, u.resources, u.type)
  else:
    return summon_row_pattern % (img, u.name, u.type)


def MakeNationFolder(era, nation):
  era_id = era.__name__.split('.')[-1]
  path = "nations/%s_%s" % (era_id, nation)
  os.mkdir(path)
  img_dir = path + '/img'
  page = path + '/page.txt'
  nation_id = getattr(era, nation)
  MakeNationImageFolder(nation_id, img_dir)
  with open(page, 'w') as f:
    f.write("\n==== Recruitable ====\n")
    f.write("\n%s\n" % unit_table_header)
    f.writelines( [MakeUnitRow(u, era_id, nation) + '\n' for u in GetUnits(nation_id)])
    f.write("\n==== Summons ====\n")
    f.write("\n%s\n" % unit_table_header)
    f.writelines( [MakeUnitRow(u, era_id, nation) + '\n' for u in GetSummons(nation_id)])
    f.write("\n==== Heroes ====\n")
    f.write("\n%s\n" % unit_table_header)
    f.writelines( [MakeUnitRow(u, era_id, nation) + '\n' for u in GetoHeroes(nation_id)])


def MakeAllFoldersForAge(era):
  for n in PublicAttr(era):
    MakeNationFolder(era, n)


def MakeAllNationFolders():
  MakeAllFoldersForAge(ea)
  MakeAllFoldersForAge(ma)
  MakeAllFoldersForAge(la)


MakeAllNationFolders()

driver.close()