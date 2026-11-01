"""Explicit local substitute for a layout absent from all archived clients."""
import copy
import json


def cup_recipe_item(read_resource):
    # ItemsShowDialog.as:658-674 requires these exact child names.
    detail=json.loads(read_resource('rsrc/json/_CupListDetailItem.json'))
    item=json.loads(read_resource('rsrc/json/_CupListItem.json'))
    rate=next(n for n in item['layout']['children'] if n.get('params',{}).get('name')=='rateGroup')
    detail['layout']['children'].append(copy.deepcopy(rate))
    detail['layout']['children'].append({
        'cls':'starling.display.Sprite','customParams':{},
        'params':{'name':'completeSprite','x':130,'y':60},
        'children':[{'cls':'starling.display.Image','customParams':{},
            'constructorParams':[{'cls':'starling.textures.Texture','textureName':'recipe0@check_on'}],
            'params':{'name':'complete'}}]})
    return json.dumps(detail,ensure_ascii=False).encode('utf-8')
