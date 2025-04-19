#!/usr/bin/env python

# JLCPCB Parts MCP Server
# Created by @nvsofts
# 
# Data is provided from JLC PCB SMD Assembly Component Catalogue
# https://github.com/yaqwsx/jlcparts

import sqlite3
import sys
import os

from mcp.server.fastmcp import FastMCP

# SQLite database path, please change this!
JLCPCB_DB_PATH = os.getenv('JLCPCB_DB_PATH')

if not JLCPCB_DB_PATH:
  print('Please set JLCPCB_DB_PATH environment value!', file=sys.stderr)
  sys.exit(1)

mcp = FastMCP('jlcpcb-parts')
conn = sqlite3.connect(JLCPCB_DB_PATH)

@mcp.tool()
def list_categories() -> str:
  """JLCPCBの部品のカテゴリ一覧を取得する"""
  result = conn.execute('SELECT id,category,subcategory FROM categories')
  return "|カテゴリID|カテゴリ名|サブカテゴリ名|\n|--|--|--|\n" + "\n".join(f'|{r[0]}|{r[1]}|{r[2]}|' for r in result)

@mcp.tool()
def list_manufacturers() -> str:
  """JLCPCBの部品のメーカー一覧を取得する"""
  result = conn.execute('SELECT id,name FROM manufacturers')
  return "|メーカーID|メーカー名|\n|--|--|\n" + "\n".join(f'|{r[0]}|{r[1]}|' for r in result)

@mcp.tool()
def get_category(category_id: int) -> str | None:
  """カテゴリIDから、カテゴリ名とサブカテゴリ名を取得する"""
  result = conn.execute('SELECT category,subcategory FROM categories WHERE id=?', [category_id]).fetchone()
  if result:
    return f'カテゴリ名：{result[0]}、サブカテゴリ名：{result[1]}'
  else:
    return None

@mcp.tool()
def get_manufacturer(manufacturer_id: int) -> str | None:
  """メーカーIDから、メーカー名を取得する"""
  result = conn.execute('SELECT name FROM manufacturers WHERE id=?', [manufacturer_id]).fetchone()
  if result:
    return result[0]
  else:
    return None

@mcp.tool()
def search_manufacturer(name: str) -> str | None:
  """メーカー名から検索を行い、メーカーIDを取得する"""
  result = conn.execute('SELECT id,name FROM manufacturers WHERE name LIKE ?', [f'%{name}%'])
  lines = []
  for r in result:
    lines.append(f'|{r[0]}|{r[1]}|')
  if lines:
    return "|メーカーID|メーカー名|\n" + "\n".join(lines)
  else:
    return None

'''
@mcp.tool()
def search_subcategories(name: str) -> str | None:
  """サブカテゴリ名（英語表記）から検索を行い、カテゴリIDを取得する"""
  result = conn.execute('SELECT id,subcategory FROM categories WHERE subcategory LIKE ?', [f'%{name}%'])
  lines = []
  for r in result:
    lines.append(f'|{r[0]}|{r[1]}|')
  if lines:
    return "|カテゴリID|サブカテゴリ名|\n" + "\n".join(lines)
  else:
    return None
'''

@mcp.tool()
def get_datasheet_url(part_id: int) -> str | None:
  """JLCPCBの部品番号から、データシートのURLを取得する、数字の部分のみだけで良い"""
  result = conn.execute('SELECT datasheet FROM components WHERE lcsc=?', [part_id]).fetchone()
  if result:
    return result[0]
  else:
    return None

@mcp.tool()
def search_parts(category_id: int, manufacturer_id: int | None, description: str | None, package: str | None, is_basic_parts: bool | None = None, is_preferred_parts: bool | None = None):
  """JLCPCBの部品を検索する、category_idとmanufacturer_idは他のツールで取得可能"""
  query = 'SELECT lcsc,category_id,manufacturer_id,mfr,basic,preferred,description,package,stock FROM components WHERE '
  where_clauses = []
  params = []
  
  where_clauses.append('category_id=?')
  params.append(category_id)
  
  if manufacturer_id is not None:
    where_clauses.append('manufacturer_id=?')
    params.append(manufacturer_id)
  if description:
    where_clauses.append('description LIKE ?')
    params.append('%' + description + '%')
  if package:
    where_clauses.append('package=?')
    params.append(package)
  
  if is_basic_parts is not None:
    where_clauses.append('basic=' + ('1' if is_basic_parts is True else '0'))
  if is_preferred_parts is not None:
    where_clauses.append('preferred=' + ('1' if is_preferred_parts is True else '0'))
  
  query += ' AND '.join(where_clauses)
  
  lines = []
  result = conn.execute(query, params)
  for r in result:
    lines.append(f'|{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}|{r[7]}|{r[8]}|')
  
  return "|部品番号|カテゴリID|メーカーID|メーカー品番|Basic Partsか|Preferred Partsか|説明|パッケージ|在庫数|\n|--|--|--|--|--|--|--|--|--|\n" + "\n".join(lines)

if __name__ == '__main__':
  mcp.run(transport='stdio')
