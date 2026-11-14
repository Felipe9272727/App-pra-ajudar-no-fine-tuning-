"""Behavioral PPO contract on a tiny synthetic network, no pretrained model."""
from types import SimpleNamespace
import math
from core import *
import importlib.util
spec=importlib.util.spec_from_file_location('native028_policy_implementation',H/'policy.py')
implementation=importlib.util.module_from_spec(spec);spec.loader.exec_module(implementation)
replay_loss=implementation.replay_loss

class Tiny(nn.Module):
    def __init__(self):
        super().__init__();self.embedding=nn.Embedding(23,7);self.head=nn.Linear(7,23,bias=False)
    def model(self,input_ids,use_cache=False):return SimpleNamespace(last_hidden_state=self.embedding(input_ids))
    def get_output_embeddings(self):return self.head


def logp(m,prefix,tokens):
    y=torch.tensor(tokens);ids=torch.tensor([prefix+tokens[:-1]]);h=hidden(m,ids,y)
    z=F.linear(h,m.head.weight)/read('config.json')['rl_temperature']
    return F.log_softmax(z,dim=-1).gather(1,y[:,None])[:,0]


def main():
    torch.set_grad_enabled(True);torch.set_num_threads(4);results=[]
    for adv,ratio,should_zero in [(1.,1.,False),(-1.,1.,False),(1.,2.,True),(-1.,.5,True)]:
        torch.manual_seed(13);m=Tiny();p=[1,2];tokens=[3,4,5]
        lp=logp(m,p,tokens);old=(lp.detach()-math.log(ratio)).tolist()
        value,stats=replay_loss(m,{'prefix_ids':p,'ids':tokens,'behavior_logp':old},adv)
        value.backward();norm=float(m.head.weight.grad.norm());previous=float(lp.detach().mean())
        if should_zero:assert norm==0.,(adv,ratio,norm)
        else:
            with torch.no_grad():
                for param in m.parameters():param.add_(param.grad,alpha=-.01)
            current=float(logp(m,p,tokens).detach().mean())
            assert (current>previous) if adv>0 else (current<previous)
        assert abs(stats['mean_ratio']-ratio)<1e-5
        results.append({'advantage':adv,'ratio':ratio,'expected_clipped_zero_gradient':should_zero,'head_grad_norm':norm})
    save('reports/policy_objective_contracts.json',{'status':'pass','no_pretrained_model_loaded':True,'no_optimizer_update_on_project_model':True,'cases':results})
    print('POLICY028_OBJECTIVE_CONTRACTS_PASS',flush=True)
if __name__=='__main__':main()
