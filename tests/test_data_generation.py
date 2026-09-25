from faker import Faker

from scripts.generate_data import generate_bom, generate_parts, generate_suppliers


def test_generated_hierarchy_has_all_five_part_levels(monkeypatch):
    class SmallSettings:
        n_suppliers = 10
        n_parts = 100
        n_bom_relationships = 180
        random_seed = 42

    import scripts.generate_data as gen

    monkeypatch.setattr(gen, "settings", SmallSettings())
    fake = Faker("en_US")
    fake.seed_instance(42)
    suppliers = generate_suppliers(fake)
    parts = generate_parts(suppliers, fake)
    bom = generate_bom(parts)
    assert set(parts.part_type) == {
        "raw_material",
        "component",
        "subassembly",
        "assembly",
        "finished_good",
    }
    assert len(bom) == 180
    assert not (bom.parent_part_id == bom.child_part_id).any()
