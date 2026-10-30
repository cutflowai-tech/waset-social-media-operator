import importlib.util,unittest
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
spec=importlib.util.spec_from_file_location('check_plan',Path(__file__).parents[1]/'chat-skill/scripts/check_plan.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PlanTests(unittest.TestCase):
    def fixture(self):
        start=datetime(2026,10,31,tzinfo=ZoneInfo('Africa/Cairo'));slots=[];current=[]
        for day in range(7):
            formats=['Story']*3+(['Post'] if day in (0,2,4,6) else [])
            for j,fmt in enumerate(formats):
                ident=str(len(slots)+1);snap=dict(format=fmt,status='Ready to Publish',code='C#'+ident,ready_file='file'+ident,caption='Reviewed',publish_at=None)
                slots.append(dict(item_id=ident,asset_id='asset'+ident,publish_at=(start+timedelta(days=day,hours=12+j*3)).isoformat(),snapshot=snap));current.append(dict(item_id=ident,**snap))
        return dict(week_start='2026-10-31',slots=slots,published_assets=[]),current
    def test_full_week(self):
        p,c=self.fixture();r=m.audit(p,c);self.assertTrue(r['complete']);self.assertTrue(r['safe_snapshot']);self.assertEqual(len(p['slots']),25)
    def test_shortage(self):
        p,c=self.fixture();p['slots'].pop();r=m.audit(p,c);self.assertFalse(r['complete']);self.assertEqual(r['shortages'],[{'format':'Post','missing':1}])
    def test_duplicate_and_published(self):
        p,c=self.fixture();p['slots'][1]['asset_id']=p['slots'][0]['asset_id'];self.assertFalse(m.audit(p,c)['structurally_valid'])
        p,c=self.fixture();p['published_assets']=['asset1'];self.assertFalse(m.audit(p,c)['structurally_valid'])
    def test_stale_status_and_time(self):
        for field,val in [('status','Published'),('publish_at','2026-11-02T12:00:00+02:00')]:
            p,c=self.fixture();c[0][field]=val;r=m.audit(p,c);self.assertEqual(r['conflicting_item_ids'],['1']);self.assertFalse(r['safe_snapshot'])
    def test_missing_connection_snapshot(self):
        p,c=self.fixture();self.assertFalse(m.audit(p,[])['safe_snapshot'])
    def test_missing_timezone(self):
        p,c=self.fixture();p['slots'][0]['publish_at']='2026-10-31T12:00:00';self.assertFalse(m.audit(p,c)['structurally_valid'])
if __name__=='__main__':unittest.main()
