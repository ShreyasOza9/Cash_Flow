from model import ModelInputs, run_model, car_emi, slab_tax

def test_basic_model():
    df, summary = run_model(ModelInputs())
    assert len(df) == 15
    assert df.iloc[0]["CTC"] > 0
    assert df.iloc[-1]["CTC"] > df.iloc[0]["CTC"]
    assert summary["final_net_worth"] >= 0

def test_car_emi():
    emi = car_emi(750000, 9, 5)
    assert 15000 < emi < 17000

def test_tax_rebate():
    assert slab_tax(1200000) == 0

if __name__ == "__main__":
    test_basic_model()
    test_car_emi()
    test_tax_rebate()
    print("All tests passed.")
