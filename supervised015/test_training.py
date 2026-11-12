"""Shared-weight/tied-weight optimizer-in-backward equivalence on a toy net."""
import copy,unittest
import torch
from torch.utils.checkpoint import checkpoint
from optimizer import BackwardAdafactor

class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.arange(64).float().reshape(8,8)/200)
        self.norm=torch.nn.Parameter(torch.ones(8))
    def forward(self,x):
        for _ in range(2):
            def block(h):return torch.tanh(h@self.weight.T)*self.norm+h
            x=checkpoint(block,x,use_reentrant=False)
        # Same weight is read again as a tied output projection.
        return checkpoint(lambda h:h@self.weight,h:=x,use_reentrant=False)

class Tests(unittest.TestCase):
    def test_update_matches_ordinary_optimizer(self):
        a=Toy();b=copy.deepcopy(a);x=torch.arange(24).float().reshape(3,8)/30
        regular=torch.optim.Adafactor(a.parameters(),lr=.01,eps=(1e-16,1e-3),beta2_decay=-.8,d=1.,weight_decay=0.,foreach=False)
        inline=BackwardAdafactor(dict(b.named_parameters()),lr=.01)
        for _ in range(3):
            inline.reset();regular.zero_grad(set_to_none=True)
            loss=(a(x).square().mean()+a(x+.2).square().mean())/2;loss.backward();regular.step()
            other=(b(x).square().mean()+b(x+.2).square().mean())/2;other.backward()
            self.assertEqual(set(inline.calls.values()),{1})
            for p,q in zip(a.parameters(),b.parameters()):self.assertTrue(torch.allclose(p,q,atol=1e-7,rtol=1e-6))
        inline.close()

if __name__=='__main__':unittest.main()
