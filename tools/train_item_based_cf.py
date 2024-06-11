from recommender.item_based_cf import ItemBasedCF


recommend_engine = ItemBasedCF()
recommend_engine.build()
recommend_engine.save()
