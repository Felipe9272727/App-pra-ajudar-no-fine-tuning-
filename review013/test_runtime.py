"""Checks causal history, reset/caps and evaluation separation, without weights."""
import unittest
from review_runtime import *

class Tests(unittest.TestCase):
    def test_causal_chunk_equivalence(self):
        x=torch.arange(4*1024,dtype=torch.float32).reshape(1,4,1024)/100
        a,h=temporal(x);history=None;parts=[]
        for i in range(4):
            b,history=temporal(x[:,i:i+1],history);parts.append(b)
        self.assertTrue(torch.equal(a,torch.cat(parts,1)))
        self.assertTrue(torch.equal(h,history))
        changed=x.clone();changed[:,3]*=100
        self.assertTrue(torch.equal(a[:,:3],temporal(changed)[0][:,:3]))
    def test_cap_and_disabled_grad(self):
        patch={'input_basis':torch.eye(1024)[:,:16],'output_map':torch.ones(16,1024)*100,
               'kind':'loop','cap':.02}
        r=Review(patch);first=torch.ones(1,3,1024);second=first*2
        out=r(first,second)
        self.assertLessEqual(float((rms(out-second)/rms(second)).max()),.020001)
        self.assertFalse(any(p.requires_grad for p in r.parameters()))
        r.reset();self.assertIsNone(r.history);self.assertEqual(r.calls,0)
    def test_no_answers_in_eval_input(self):
        self.assertEqual(eval_inputs({'prompt':'problem','solution':'SECRET','cases':['SECRET']}),'problem')
    def test_zero_patch_identity(self):
        p={'input_basis':torch.eye(2048)[:,:16],'output_map':torch.zeros(16,1024),'kind':'joint','cap':.02}
        r=Review(p);x=torch.arange(1024).float().reshape(1,1,1024)
        self.assertTrue(torch.equal(r(x,x),x))
    def test_family_and_ast_disjoint(self):
        rows={s:json.loads((HERE/(s+'.json')).read_text()) for s in ['train','validation','test']}
        self.assertEqual([len(rows[s]) for s in rows],[120,40,40])
        for a,b in [('train','validation'),('train','test'),('validation','test')]:
            self.assertFalse({r['family'] for r in rows[a]}&{r['family'] for r in rows[b]})
            self.assertFalse({r['solution_ast_sha256'] for r in rows[a]}&{r['solution_ast_sha256'] for r in rows[b]})

if __name__=='__main__':unittest.main()
