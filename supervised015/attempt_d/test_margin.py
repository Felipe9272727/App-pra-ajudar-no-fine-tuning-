"""Compare the sparse active-competitor subgradient with full-vocabulary autograd."""
import torch,unittest
class TestMargin(unittest.TestCase):
    def test_sparse_subgradient_matches_dense(self):
        torch.set_num_threads(1);torch.manual_seed(12)
        x=torch.randn(7,12);r=torch.randn(7,8);embedding=torch.randn(31,8);gold=torch.arange(7)
        a=torch.randn(8,12,requires_grad=True);b=a.detach().clone().requires_grad_()
        def hidden(w):
            h=r+x@w.T;return h*torch.rsqrt(h.square().mean(-1,keepdim=True)+1e-5)
        h=hidden(a);logits=h@embedding.T;chosen=logits.gather(1,gold[:,None]).squeeze(1);masked=logits.clone();masked.scatter_(1,gold[:,None],float('-inf'));other,c=masked.max(-1)
        margin=chosen-other;dense=torch.relu(10-margin).square().mean();ga=torch.autograd.grad(dense,a)[0]
        h2=hidden(b);pair=torch.stack([embedding[gold],embedding[c.detach()]],1);p=torch.bmm(pair,h2.unsqueeze(-1)).squeeze(-1);s=p[:,0]-p[:,1]
        straight=s-s.detach()+margin.detach();sparse=torch.relu(10-straight).square().mean();gb=torch.autograd.grad(sparse,b)[0]
        torch.testing.assert_close(dense,sparse);torch.testing.assert_close(ga,gb,atol=1e-5,rtol=1e-5)
if __name__=='__main__':unittest.main()
