import os
import tempfile
import unittest
import random

import numpy as np
import scipy
from hnsw_als import HNSWLibAlternatingLeastSquares
from implicit.nearest_neighbours import bm25_weight

USERS = 30
ITEMS = 40
FACTORS = 16
TEST = os.path.basename(__file__)


class TestHNSW(unittest.TestCase):
    def setUp(self):
        self.model = HNSWLibAlternatingLeastSquares(
            factors=FACTORS, dtype=np.float32, num_threads=2
        )
        self.model.set_user_factors(np.random.rand(USERS, FACTORS) * 0.01)
        self.model.set_item_factors(np.random.rand(ITEMS, FACTORS) * 0.01)

    def test_save_indexes_empty(self):
        model = HNSWLibAlternatingLeastSquares(factors=FACTORS, dtype=np.float32)
        with tempfile.TemporaryDirectory(
            prefix=TEST, suffix="test_save_indexes_empty"
        ) as tmp:
            model.save_indexes(tmp)

    def test_load_empty(self):
        with tempfile.TemporaryDirectory(prefix=TEST, suffix="test_load_empty") as tmp:
            model = HNSWLibAlternatingLeastSquares(factors=FACTORS, dtype=np.float32)
            model.load_indexes(tmp)

    def test_init(self):
        self.assertEqual(USERS, self.model.similar_users_index.get_current_count())
        self.assertEqual(USERS, len(self.model.user_factors))
        self.assertEqual(ITEMS, self.model.similar_items_index.get_current_count())
        self.assertEqual(ITEMS, self.model.recommend_index.get_current_count())
        self.assertEqual(ITEMS, len(self.model.item_factors))

    def test_fit(self):
        PLAYS = 5
        plays = scipy.sparse.csr_matrix(
            (
                np.random.randint(1, 10, size=USERS * PLAYS),
                (
                    np.random.randint(0, ITEMS, size=USERS * PLAYS),
                    list(range(USERS)) * PLAYS,
                ),
            ),
            shape=(ITEMS, USERS),
        )
        Ciu = bm25_weight(plays, K1=100, B=0.8)
        self.model.fit(Ciu, show_progress=False)
        self.assertEqual(USERS, self.model.similar_users_index.get_current_count())
        self.assertEqual(USERS, len(self.model.user_factors))
        self.assertEqual(ITEMS, self.model.similar_items_index.get_current_count())
        self.assertEqual(ITEMS, self.model.recommend_index.get_current_count())
        self.assertEqual(ITEMS, len(self.model.item_factors))

    def test_save_indexes(self):
        with tempfile.TemporaryDirectory(
            prefix=TEST, suffix="test_save_indexes"
        ) as tmp:
            self.model.save_indexes(tmp)
            self.assertTrue(
                os.path.isfile(os.path.join(tmp, "similar_items_index.bin%s" % FACTORS))
            )
            self.assertTrue(
                os.path.isfile(os.path.join(tmp, "similar_users_index.bin%s" % FACTORS))
            )
            self.assertTrue(
                os.path.isfile(
                    os.path.join(tmp, "recommend_index.bin%s" % (FACTORS + 1))
                )
            )

    def test_save_load(self):
        with tempfile.TemporaryDirectory(prefix=TEST, suffix="test_save_load") as tmp:
            self.model.save_indexes(tmp)
            self.model = HNSWLibAlternatingLeastSquares(
                factors=FACTORS, dtype=np.float32
            )
            self.model.load_indexes(tmp)
        self.test_init()

    def test_similar_items(self):
        lst = self.model.similar_items_by_factors(np.random.rand(FACTORS))
        self.assertTrue(lst)
        self.assertIsInstance(next(lst)[0], (int, np.integer))
        self.assertIsInstance(next(lst)[1], (float, np.float32))

    def test_similar_users(self):
        lst = self.model.similar_users_by_factors(np.random.rand(FACTORS))
        self.assertTrue(lst)
        self.assertIsInstance(next(lst)[0], (int, np.integer))
        self.assertIsInstance(next(lst)[1], (float, np.float32))

    def test_similar_users_empty(self):
        self.model.set_user_factors([])
        lst = self.model.similar_users_by_factors(np.random.rand(FACTORS))
        self.assertFalse(lst)

    def test_add_item_to_empty(self):
        self.model = HNSWLibAlternatingLeastSquares(factors=FACTORS)
        self.test_add_item(0)

    def test_add_item_to_empty_similar_items(self):
        self.test_add_item_to_empty()
        lst = self.model.similar_items_by_factors(np.random.rand(FACTORS))
        self.assertTrue(lst)

    def test_add_item_to_empty_recommend(self):
        self.test_add_item_to_empty()
        lst = self.model.recommend(
            0,
            self.dummy_user_plays_csr(items=1, k=1),
            recalculate_user=True,
            filter_already_liked_items=False,
        )
        self.assertTrue(lst)

    def test_add_items_to_empty(self):
        self.model = HNSWLibAlternatingLeastSquares(factors=FACTORS)
        self.test_add_items(0)

    def test_add_user_to_empty(self):
        self.model = HNSWLibAlternatingLeastSquares(factors=FACTORS)
        self.test_add_user(0)

    def test_add_user_to_empty_similar_users(self):
        self.test_add_user_to_empty()
        lst = self.model.similar_users_by_factors(np.random.rand(FACTORS))
        self.assertTrue(lst)

    def test_add_users_to_empty(self):
        self.model = HNSWLibAlternatingLeastSquares(factors=FACTORS)
        self.test_add_users(0)

    def test_add_item(self, items=ITEMS):
        count = self.model.add_items(np.random.rand(FACTORS))
        self.assertEqual(items + 1, count)
        self.assertEqual(items + 1, self.model.similar_items_index.get_current_count())
        self.assertEqual(items + 1, self.model.recommend_index.get_current_count())
        self.assertEqual(items + 1, len(self.model.item_factors))

    def test_add_items(self, items=ITEMS):
        count = self.model.add_items(np.random.rand(2, FACTORS))
        self.assertEqual(items + 2, count)
        self.assertEqual(items + 2, self.model.similar_items_index.get_current_count())
        self.assertEqual(items + 2, self.model.recommend_index.get_current_count())
        self.assertEqual(items + 2, len(self.model.item_factors))

    def test_add_user(self, users=USERS):
        count = self.model.add_users(np.random.rand(FACTORS))
        self.assertEqual(users + 1, count)
        self.assertEqual(users + 1, self.model.similar_users_index.get_current_count())
        self.assertEqual(users + 1, len(self.model.user_factors))

    def test_add_users(self, users=USERS):
        count = self.model.add_users(np.random.rand(2, FACTORS))
        self.assertEqual(users + 2, count)
        self.assertEqual(users + 2, self.model.similar_users_index.get_current_count())
        self.assertEqual(users + 2, len(self.model.user_factors))

    @staticmethod
    def dummy_user_plays_csr(items: int = ITEMS, k: int = 2):
        artist_ids = random.sample(range(items), k=k)
        return scipy.sparse.coo_matrix(
            ([444.0] * len(artist_ids), ([0] * len(artist_ids), artist_ids)),
            shape=(1, items),
        ).tocsr()

    def test_recommend(self):
        lst = self.model.recommend(0, self.dummy_user_plays_csr())
        self.assertTrue(lst)
        self.assertIsInstance(lst[0][0], (int, np.integer))
        self.assertIsInstance(lst[9][1], (float, np.float32))

    def test_recommend_recalc(self):
        lst = self.model.recommend(
            0, self.dummy_user_plays_csr(), recalculate_user=True
        )
        self.assertTrue(lst)
        self.assertIsInstance(lst[0][0], (int, np.integer))
        self.assertIsInstance(lst[9][1], (float, np.float32))


if __name__ == "__main__":
    unittest.main()
