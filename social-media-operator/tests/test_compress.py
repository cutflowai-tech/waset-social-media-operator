import importlib.util, json, subprocess, tempfile, unittest, hashlib
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('compress',Path(__file__).parents[1]/'mac-tool'/'compress.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def ff(*args):
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y',*map(str,args)],check=True)

class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.out=self.root/'out';self.out.mkdir()
    def tearDown(self):self.temp.cleanup()
    def make(self,name='اختبار فيديو.mov',size='320x180',audio=True):
        p=self.root/name
        args=['-f','lavfi','-i',f'testsrc2=size={size}:rate=30:duration=2']
        if audio:args+=['-f','lavfi','-i','sine=frequency=440:duration=2']
        args+=['-c:v','qtrle','-threads','1']
        if audio:args+=['-c:a','pcm_s16le']
        ff(*args,p);return p
    def test_portrait_landscape_audio_and_silent(self):
        for i,(size,audio) in enumerate([('320x180',True),('180x320',False)]):
            p=self.make(f'اسم {i}.mov',size,audio);before=hashlib.sha256(p.read_bytes()).hexdigest()
            row=c.process(p,self.out,limit=150000,target=130000)
            self.assertEqual(row['status'],'compressed',row)
            self.assertLess(row['after_bytes'],150000)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
            self.assertEqual(c.probe(Path(row['output']))['audio'],int(audio))
    def test_small_corrupt_duplicates(self):
        p=self.make();row=c.process(p,self.out);self.assertEqual(row['status'],'already_under_limit')
        bad=self.root/'broken.mp4';bad.write_bytes(b'not video');self.assertEqual(c.process(bad,self.out)['status'],'failed')
        a=c.process(p,self.out,150000,130000);b=c.process(p,self.out,150000,130000)
        self.assertEqual(a['status'],'compressed');self.assertEqual(b['status'],'compressed');self.assertNotEqual(a['output'],b['output'])
        c.reports([row,a,b],self.out);self.assertEqual(len(json.loads((self.out/'report.json').read_text())),3)
    def test_rotation(self):
        source=self.make('base.mov');rotated=self.root/'rotated.mov'
        ff('-display_rotation','90','-i',source,'-c','copy',rotated)
        row=c.process(rotated,self.out,150000,130000)
        self.assertEqual(row['status'],'compressed',row);self.assertEqual(row['dimensions'],'180×320')
    def test_retry_and_failure_are_bounded(self):
        p=self.make();calls=[]
        def fake_encode(src,out,info,rate,log):calls.append(rate);out.write_bytes(b'X'*160000)
        with patch.object(c,'encode',side_effect=fake_encode):
            row=c.process(p,self.out,150000,130000)
        self.assertEqual(len(calls),2);self.assertEqual(row['status'],'failed');self.assertLess(calls[1],calls[0]);self.assertFalse(list(self.out.glob('*.mp4')))
    def test_real_300mb_boundary(self):
        p=self.root/'large1080.avi'
        ff('-f','lavfi','-i','testsrc2=size=1920x1080:rate=30:duration=4','-c:v','rawvideo','-pix_fmt','yuv420p',p)
        self.assertGreaterEqual(p.stat().st_size,300000000)
        row=c.process(p,self.out)
        self.assertEqual(row['status'],'compressed',row);self.assertLess(row['after_bytes'],300000000);self.assertEqual(row['dimensions'],'1920×1080')

if __name__=='__main__':unittest.main(verbosity=2)
