"""Derived SCORE bits for pre-execution rejection, never invented executions."""
def scored_case_bits(row):
    if 'case_passed' in row:
        bits=row['case_passed'];assert len(bits)==row['total'];assert sum(bits)==row['passed']
        return bits
    # Canonical judge returns early, without per-case execution, in these cases.
    assert row['category'] in ['SyntaxError','ContractError'],row
    assert row['passed']==0 and row['all_passed'] is False,row
    return [False]*row['total']
