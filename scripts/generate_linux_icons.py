#!/usr/bin/env python3
"""Derive Linux assets from the approved Icon Composer vectors and color recipe."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def srgb(rgb, p3=False):
    if p3:
        lin = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        lin = [sum(a*b for a,b in zip(row,lin)) for row in
               ((1.224745,-.224904,0),(-.042058,1.042081,0),(-.019642,-.078655,1.098537))]
        rgb = [12.92*v if v <= .0031308 else 1.055*max(0,v)**(1/2.4)-.055 for v in lin]
    return '#'+''.join(f'{round(max(0,min(1,v))*255):02x}' for v in rgb)


def generate():
    master = ROOT / 'payloads/linux-identity/master'
    out = ROOT / 'payloads/linux-identity/generated'
    out.mkdir(parents=True, exist_ok=True)
    plane = ET.fromstring((master/'Plane.svg').read_text())
    oval = ET.fromstring((master/'Oval.svg').read_text())
    recipe = json.loads((master/'icon.json').read_text())
    colors = recipe['groups'][0]['layers'][1]['fill-specializations'][0]['value']['linear-gradient']
    converted=[]
    for c in colors:
        space,values=c.split(':')
        converted.append(srgb([float(x) for x in values.split(',')[:3]], space=='display-p3'))
    circle=oval.find('.//'+NS+'circle')
    attrs=' '.join(f'{k}="{circle.attrib[k]}"' for k in ('cx','cy','r'))
    geometry=''.join(ET.tostring(x,encoding='unicode') for x in plane)
    gradient=f'<defs><linearGradient id="brand" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{converted[0]}"/><stop offset="1" stop-color="{converted[1]}"/></linearGradient></defs>'
    artwork=gradient+f'<circle {attrs} fill="url(#brand)"/>'+geometry
    def svg(view,body):
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="{view}">{body}</svg>\n'
    (out/'app.svg').write_text(svg('0 0 1024 1024',artwork))
    (out/'app-no-margin.svg').write_text(svg('101.5 101.5 821 821',artwork))
    for size in (16,32,48,64,128,256,512):
        for suffix,factor in (('',1),('@2x',2)):
            subprocess.run(['rsvg-convert','-w',str(size*factor),'-h',str(size*factor),str(out/'app.svg'),'-o',str(out/f'icon{size}{suffix}.png')],check=True)
    for name,source in (('logo_256.png','app.svg'),('logo_256_no_margin.png','app-no-margin.svg')):
        subprocess.run(['rsvg-convert','-w','256','-h','256',str(out/source),'-o',str(out/name)],check=True)
    mono=geometry.replace('#FFFFFF','#000000')
    # State badges are separate from the unchanged canonical plane silhouette.
    variants={'':mono,'_attention':mono+'<circle cx="736" cy="736" r="55" fill="#000000"/>',
              '_mute':'<g opacity="0.55">'+mono+'</g><path d="M690 690 L775 775 M775 690 L690 775" stroke="#000000" stroke-width="22"/>'}
    for suffix,body in variants.items():
        (out/f'tray_monochrome{suffix}.svg').write_text(svg('256 300 560 560',body))
    print('Generated 16 PNGs and three symbolic variants from approved Reveal geometry')

if __name__ == '__main__':
    generate()
