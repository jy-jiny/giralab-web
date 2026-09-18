#!/usr/bin/env python3
"""Lunch Rush: original 156 BPM / 32-bar restaurant instrumental.
All instruments are synthesized from oscillators/noise. No recordings, samples or vocals.
Dependencies: numpy, scipy, ffmpeg. Circular tails preserve a musical loop.
"""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR=44100
BPM=156
BARS=32
BEAT=60/BPM
N=round(BARS*4*BEAT*SR)
rng=np.random.default_rng(1562026)
audio=np.zeros((N,2),np.float64)
counts={}

def add(y, beat, gain=1, pan=0, kind='note'):
    counts[kind]=counts.get(kind,0)+1
    start=round(beat*BEAT*SR)%N
    gains=np.array([math.cos((pan+1)*math.pi/4),math.sin((pan+1)*math.pi/4)])
    z=y[:,None]*gains[None,:]*gain
    end=start+len(z)
    if end<=N:audio[start:end]+=z
    else:audio[start:]+=z[:N-start];audio[:end-N]+=z[N-start:]

def tone(note, beat, duration, gain, voice='mallet', pan=0):
    f=440*2**((note-69)/12)
    hold=duration*BEAT
    release={'mallet':.22,'clav':.08,'brass':.08,'bass':.065,'reed':.09}[voice]
    t=np.arange(round((hold+release)*SR))/SR
    gate=np.minimum(t/.003,1)*np.minimum(np.maximum((hold+release-t)/release,0),1)
    if voice=='mallet':
        y=(np.sin(2*np.pi*f*t)*np.exp(-t/(hold*.8+.08))+.32*np.sin(2*np.pi*f*3.99*t)*np.exp(-t/.04)+.085*np.sin(2*np.pi*f*9.97*t)*np.exp(-t/.012))*gate
    elif voice=='clav':
        y=sum(a*np.sin(2*np.pi*f*k*t)*np.exp(-t/(.05+.11/k)) for k,a in [(1,.7),(2,.32),(3,.26),(4,.13),(5,.075)])*gate
    elif voice=='bass':
        bend=.7*(1-np.exp(-t*70))
        phase=2*np.pi*(f*t+bend*.04)
        y=(np.sin(phase)+.32*np.sin(2*phase)*np.exp(-t*8)+.13*np.sin(3*phase)*np.exp(-t*12))*gate*np.exp(-t*.8)
    else:
        vib=.0018*np.sin(2*np.pi*5.2*t)*np.minimum(t/.08,1)
        phase=2*np.pi*np.cumsum(f*(1+vib))/SR
        brightness=(1-np.exp(-t*70))*np.exp(-t*3.5)
        y=np.sin(phase)
        for k,a in [(2,.40),(3,.30),(4,.15),(5,.085),(6,.04)]:y+=a*np.sin(k*phase)*brightness
        y*=gate*(1-np.exp(-t*180))*np.exp(-t*1.2)
    add(y,beat,gain,pan,voice)

def noise_filter(n,cut,mode):
    return sosfilt(butter(2,cut,btype=mode,fs=SR,output='sos'),rng.standard_normal(n))

def drum(kind,beat,gain=1,pan=0):
    length={'kick':.24,'snare':.14,'hat':.047,'open':.14,'clack':.06,'bell':.45,'tom':.15}[kind]
    t=np.arange(round(length*SR))/SR
    if kind=='kick':
        freq=49+100*np.exp(-t*44)
        y=np.sin(2*np.pi*np.cumsum(freq)/SR)*np.exp(-t*19)+.028*noise_filter(len(t),1500,'highpass')*np.exp(-t*240)
    elif kind=='snare':
        y=.50*noise_filter(len(t),[900,9000],'bandpass')*np.exp(-t*34)+.26*np.sin(2*np.pi*185*t)*np.exp(-t*40)
    elif kind in ('hat','open'):
        metal=sum(np.sin(2*np.pi*f*t) for f in [4301,6157,7927])/3
        y=(.30*noise_filter(len(t),6000,'highpass')+.13*metal)*np.exp(-t*(86 if kind=='hat' else 24))
    elif kind=='clack':
        y=(np.sin(2*np.pi*1640*t)+.5*np.sin(2*np.pi*2410*t))*np.exp(-t*110)*.33
    elif kind=='bell':
        y=(np.sin(2*np.pi*1318.51*t)+.23*np.sin(2*np.pi*3551*t))*np.exp(-t*12)*.40
    else:y=np.sin(2*np.pi*np.cumsum(100+90*np.exp(-t*30))/SR)*np.exp(-t*26)*.6
    y*=np.minimum(t/.0015,1)*np.minimum((length-t)/.008,1)
    add(y,beat,gain,pan,kind)

roots=[38,34,31,33,29,36,38,33]
chords=[[62,65,69,72],[62,65,67,70],[62,65,67,70],[61,64,67,71],[60,64,65,69],[60,64,67,70],[62,65,69,72],[61,64,67,70]]
melodies=[[69,74,77,76,74,69,72,74],[65,70,74,72,70,77,75,74],[74,79,77,74,70,69,67,69],[73,76,79,77,76,74,73,69],[69,72,77,76,74,72,69,72],[67,72,76,74,72,70,67,64],[65,69,74,77,76,74,72,69],[67,70,73,76,74,73,71,73]]
# A / A variation / call-and-response bridge / full lunch-rush reprise.
for bar in range(BARS):
    part=bar//8;j=bar%8;b=bar*4
    root=roots[j];notes=melodies[j];voicing=chords[j]
    for q in [0,1.5,2,3.25] if part!=2 else [0,2]:drum('kick',b+q,.37 if q in [0,2] else .23)
    for q in [1,3]:drum('snare',b+q,.43 if part!=2 else .30,.06)
    for k in range(8):
        q=k*.5+(.025 if k%2 else 0)
        drum('hat',b+q,.42 if k%2 else .31,-.26)
    if part in [1,3]:
        for q in [1.75,2.75,3.75]:drum('hat',b+q,.17,.36)
    for q in [.75,2.5]:drum('clack',b+q,.26,.40)
    if j in [3,7]:
        for k,q in enumerate([3.0,3.25,3.5,3.75]):drum('snare' if k<2 else 'tom',b+q,.17+k*.035,-.2+k*.15)
        drum('open',b+3.5,.24,-.25)
    if j==0:drum('bell',b,.12,.25)
    bass_pattern=[(0,root,.43),(.75,root+12,.19),(1.5,root+7,.36),(2,root,.42),(2.75,root+10,.19),(3.25,root+12,.22),(3.75,roots[(j+1)%8]-1,.19)]
    for q,pitch,dur in bass_pattern:tone(pitch,b+q,dur,.20,'bass',-.08)
    for q in [.5,1.75,2.5,3.5]:
        for i,note in enumerate(voicing[:3] if part==0 else voicing):tone(note,b+q+i*.007,.14,.065 if part!=2 else .05,'clav',-.30)
    if part!=2:
        rhythm=[0,.5,.75,1.5,2,2.5,3,3.5] if j%2==0 else [.25,.75,1,1.75,2.25,2.75,3.25,3.75]
        for k,(q,note) in enumerate(zip(rhythm,notes)):
            if part==0 and j in [3,7] and k in [4,6]:continue
            tone(note,b+q,.26 if k%3 else .38,.135 if part!=3 else .147,'mallet',.17)
        if part in [1,3] and j%2:
            for q,k in [(1.5,1),(3,4)]:
                for n in [voicing[0],voicing[2]]:tone(n,b+q,.24,.064,'brass',-.17)
    else:
        for k,q in enumerate([.5,1.25,2.5,3.25]):tone(notes[k*2],b+q,.30,.095,'reed',.15)
        for k,q in enumerate([0,.75,2,2.75]):tone(voicing[k]+12,b+q,.22,.055,'mallet',-.27)
    if part==3 and j in [2,3,6,7]:
        for k,q in enumerate([.25,1.25,2.25,3.25]):tone(voicing[k]+12,b+q,.14,.037,'clav',.38)

dry=audio.copy()
for delay,level in [(.041,.075),(.083,.047),(.127,.027)]:audio+=np.roll(dry[:,::-1],round(delay*SR),axis=0)*level
# Filter a complete preceding cycle so filter startup does not interrupt the loop.
audio=sosfilt(butter(2,32,btype='highpass',fs=SR,output='sos'),np.concatenate([audio,audio]),axis=0)[N:]
audio=np.tanh(audio*1.13);audio-=audio.mean(axis=0);audio*=.76/np.max(np.abs(audio))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='release-assets');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    wav=out/'lunch-rush-v1.wav';ogg=out/'lunch-rush-v1.ogg'
    wavfile.write(wav,SR,np.int16(np.clip(audio,-1,1)*32767))
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libvorbis','-q:a','5','-metadata','title=Lunch Rush','-metadata','artist=GiraLab original soundtrack',str(ogg)],check=True)
    meta={'title':'Lunch Rush','version':1,'bpm':BPM,'bars':BARS,'sample_rate':SR,'samples':N,'duration_seconds':N/SR,'channels':2,'peak_dbfs':round(20*np.log10(np.max(np.abs(audio))),2),'rms_dbfs':round(20*np.log10(np.sqrt(np.mean(audio**2))),2),'loop_boundary_jump':float(np.max(np.abs(audio[-1]-audio[0]))),'events':counts,'source':'Original score; procedural instruments, no third-party recordings or samples','ogg_sha256':hashlib.sha256(ogg.read_bytes()).hexdigest(),'pcm_sha256':hashlib.sha256(wav.read_bytes()).hexdigest()}
    assert meta['loop_boundary_jump']<.015 and -22<meta['rms_dbfs']<-12 and meta['peak_dbfs']<-2
    (out/'lunch-rush-v1.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
