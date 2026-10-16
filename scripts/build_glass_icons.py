from pathlib import Path
from PIL import Image, ImageFilter, ImageChops
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import numpy as np, cairosvg, io, urllib.request, hashlib

NAMES="proxy auto fallback adblock final ai google microsoft apple youtube netflix disney primevideo spotify tiktok twitch hbo abema bahamut dazn bbc bilibili telegram whatsapp instagram facebook twitter discord line reddit linkedin steam paypal".split()
BRIGHTS="#1688F5 #EBA52E #15C494 #ED3E67 #9959EE #19BCBA #4085E1 #1479C9 #93A1BB #F83850 #322037 #1D58E2 #088DDA #0BDB70 #36354A #9A57ED #7842D1 #12C8B4 #249FDE #465569 #EA475E #F36EB7 #07B8F5 #29CF7B #E852D1 #2985FF #3D4559 #6E82F3 #1DC85C #FF7339 #139BD8 #217EE8 #1F9EE9".split()
DARKS="#08317B #603508 #075345 #6D122C #30136C #063D48 #172338 #0B264E #313645 #650B1E #0C0914 #061C5A #07365A #034828 #0D0C16 #311354 #21134C #053F3A #073654 #1A2131 #5A182D #621944 #053B72 #045129 #55196A #09265B #111821 #1C296F #045B2E #732516 #073C67 #0B2455 #062B60".split()
COLORS=dict(zip(NAMES,zip(DARKS,BRIGHTS)))
FONT=Path("SimpleIcons.otf")
if not FONT.exists():
    url="https://repo.huaweicloud.com/CTAN/fonts/simpleicons/opentype/SimpleIcons.otf"
    urllib.request.urlretrieve(url,FONT)
GL=TTFont(FONT).getGlyphSet()
SPECIAL={
"proxy":'<circle cx="128" cy="128" r="76" fill="none" stroke="white" stroke-width="18"/><path d="M54 102H112V80L145 114L112 147V124H54Z"/><path d="M202 153H144V175L111 142L144 109V131H202Z"/>',
"auto":'<path d="M145 24L80 132H125L105 232L184 109H137Z"/><rect x="27" y="76" width="51" height="15" rx="7"/><rect x="19" y="110" width="47" height="15" rx="7"/>',
"fallback":'<rect x="34" y="46" width="152" height="35" rx="17"/><rect x="34" y="109" width="152" height="35" rx="17"/><rect x="34" y="172" width="110" height="35" rx="17"/><path d="M143 189L169 212L221 153" fill="none" stroke="white" stroke-width="17" stroke-linecap="round"/>',
"adblock":'<path d="M128 22L219 61V126C219 184 189 216 128 240C67 216 37 184 37 126V61Z"/><circle cx="128" cy="126" r="47" fill="none" stroke="white" stroke-width="15"/><rect x="99" y="120" width="58" height="14" rx="7"/>',
"final":'<path d="M68 128C48 85 32 80 26 104C18 137 58 178 102 144L160 103C204 71 240 99 231 134C221 172 188 174 164 127" fill="none" stroke="white" stroke-width="29" stroke-linecap="round"/><path d="M202 98L232 133L198 158" fill="none" stroke="white" stroke-width="21" stroke-linecap="round"/>',
"microsoft":'<rect x="24" y="24" width="94" height="94" rx="9"/><rect x="138" y="24" width="94" height="94" rx="9"/><rect x="24" y="138" width="94" height="94" rx="9"/><rect x="138" y="138" width="94" height="94" rx="9"/>',
"disney":'<path d="M25 116C56 71 101 47 157 60C194 69 216 92 230 105" fill="none" stroke="white" stroke-width="9"/><path d="M92 91C143 79 164 122 142 171C119 218 54 221 53 174C53 143 83 136 105 145C132 157 124 186 103 188" fill="none" stroke="white" stroke-width="24"/><path d="M192 148V192M170 170H214" fill="none" stroke="white" stroke-width="13"/>',
"primevideo":'<rect x="22" y="46" width="210" height="151" rx="33"/><path d="M98 74V164L163 119Z" fill="none" stroke="white" stroke-width="11"/><path d="M82 219Q131 242 185 213" fill="none" stroke="white" stroke-width="13"/>',
"abema":'<path d="M57 94L49 41L91 78Q128 60 165 78L206 41L199 94Q232 131 206 187Q186 222 127 224Q68 222 49 187Q23 131 57 94Z"/><circle cx="100" cy="151" r="9" fill="#115555"/><circle cx="155" cy="151" r="9" fill="#115555"/>',
"bahamut":'<path d="M55 29H128C188 29 217 51 209 88C205 110 189 123 172 128C213 134 222 172 202 203C184 231 140 229 55 229Z M94 67V111H134C181 111 180 67 134 67Z M94 147V191H139C184 191 184 147 139 147Z" fill-rule="evenodd"/>',
"bbc":'<rect x="17" y="76" width="66" height="102" rx="10"/><rect x="95" y="76" width="66" height="102" rx="10"/><rect x="173" y="76" width="66" height="102" rx="10"/>',
"linkedin":'<circle cx="56" cy="61" r="20"/><rect x="38" y="95" width="36" height="133" rx="4"/><path d="M98 97H134V118Q150 92 177 92C222 92 231 125 231 169V228H193V174C193 151 190 133 172 133C149 133 136 151 136 176V228H98Z"/>',
}
def mark(name):
    if name in SPECIAL:
        svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><g fill="white" stroke-linejoin="round">'+SPECIAL[name]+'</g></svg>'
    else:
        glyph=('openai' if name=='ai' else 'x' if name=='twitter' else name)+'icon'
        if glyph not in GL: raise RuntimeError("Missing icon font glyph "+glyph)
        pen=SVGPathPen(GL);bounds=BoundsPen(GL);GL[glyph].draw(pen);GL[glyph].draw(bounds)
        x,y,X,Y=bounds.bounds;scale=390/max(X-x,Y-y)
        tx=256-(x+X)*scale/2;ty=256+(y+Y)*scale/2
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="{pen.getCommands()}" transform="translate({tx},{ty}) scale({scale},{-scale})" fill="white"/></svg>'
    data=cairosvg.svg2png(bytestring=svg.encode(),output_width=512,output_height=512)
    im=Image.open(io.BytesIO(data)).convert('RGBA').getchannel('A')
    box=im.getbbox()
    if not box: raise RuntimeError("Empty glyph "+name)
    im=im.crop(box); f=min(306/im.width,306/im.height)
    if name in ("hbo","bbc","dazn","linkedin","twitter"):f*=.93
    w,h=round(im.width*f),round(im.height*f)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    m=Image.new('L',(512,512));m.paste(im,((512-w)//2,(512-h)//2))
    return m

def rgb(s):return np.array([int(s[i:i+2],16) for i in (1,3,5)],np.float32)
Y,X=np.mgrid[:512,:512]
outdir=Path("icons");outdir.mkdir(exist_ok=True)
for name in NAMES:
    dark,bright=map(rgb,COLORS[name])
    bg=Image.new('L',(512,512))
    from PIL import ImageDraw
    ImageDraw.Draw(bg).rounded_rectangle((30,30,482,480),radius=103,fill=255)
    alpha=np.asarray(bg,dtype=np.float32)/255
    image=Image.new('RGBA',(512,512))
    glow_layer=Image.new('RGBA',(512,512),tuple(map(int,bright))+(0,))
    glow_layer.putalpha(bg.filter(ImageFilter.GaussianBlur(22)).point(lambda v:int(v*.28)))
    image=Image.alpha_composite(image,glow_layer)
    w=np.clip(.10+.82*(Y-30)/450+.07*X/512,0,1)
    gradient=dark[None,None,:]*(1-w[:,:,None])+bright[None,None,:]*w[:,:,None]
    light=np.exp(-((X-140)**2/235**2+(Y-100)**2/170**2))*.31
    gradient=np.clip(gradient+(255-gradient)*light[:,:,None],0,255)
    panel=np.zeros((512,512,4),np.uint8);panel[:,:,:3]=gradient.astype('uint8');panel[:,:,3]=(alpha*255).astype('uint8')
    image=Image.alpha_composite(image,Image.fromarray(panel,'RGBA'))
    border=ImageChops.subtract(bg,bg.filter(ImageFilter.MinFilter(13)))
    edge=Image.new('RGBA',(512,512),(238,247,255,0));edge.putalpha(border.point(lambda v:int(v*.69)))
    image=Image.alpha_composite(image,edge)
    glyph=mark(name)
    shade=Image.new('RGBA',(512,512),(5,15,40,0))
    shade.putalpha(glyph.filter(ImageFilter.GaussianBlur(8)).transform((512,512),Image.Transform.AFFINE,(1,0,-2,0,1,-8)).point(lambda v:int(v*.45)))
    image=Image.alpha_composite(image,shade)
    if name=="netflix":col=(243,35,54)
    elif name=="spotify":col=(17,75,39)
    else:col=(246,251,255)
    foreground=Image.new('RGBA',(512,512),col+(0,));foreground.putalpha(glyph)
    image=Image.alpha_composite(image,foreground)
    image.save(outdir/(name+".png"),optimize=True)
files=list(outdir.glob("*.png"))
assert len(files)==33
assert len({hashlib.sha256(f.read_bytes()).hexdigest() for f in files})==33
print("PASS: 33 individual PNGs")
