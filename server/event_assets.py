"""Local aliases for the first festival atlas; original PNG/XML stay read-only."""
import copy
import xml.etree.ElementTree as ET
from .library import c

PATH='rsrc/atlas/event0.xml'
ALIASES={'banner01':'btn_benri','balloon_item':'balloon_shell','item':'shell'}


def asset(raw):
    root=ET.fromstring(raw)
    nodes={x.attrib['name']:x for x in root}
    for target,source in ALIASES.items():
        target,source='event0@'+target,'event0@'+source
        if target not in nodes:
            node=copy.deepcopy(nodes[source])
            node.set('name',target)
            root.append(node)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def short_hash(data):
    # muku/util/ObjectUtil.as:138-169; ByteArray big-endian, zero padded,
    # signed int32 overflow. This helper deliberately only supports short XML.
    if len(data)>51200:raise ValueError('event XML exceeds short hash limit')
    data+=b'\0'*(-len(data)%4)
    value=0
    for i in range(0,len(data),4):
        value=(31*value+int.from_bytes(data[i:i+4],'big'))&0xffffffff
    return value if value<0x80000000 else value-0x100000000


def metadata(d,data):
    info=next((x for x in d.fileInfos.value if x.path==PATH),None)
    if info is None:
        info=c.FileInfoDef(path=PATH,size=0,hash=0,hasLocale=False)
        d.fileInfos.value.append(info)
    info.size,info.hash=len(data),short_hash(data)
