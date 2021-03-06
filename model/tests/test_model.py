import shutil
import tempfile
import unittest

import numpy
import scipy

from model import Model

ARTISTS = 300
PLAYLISTS = 11


class TestModel(unittest.TestCase):
    TEST_MODEL = "/tmp/TestModel"

    @classmethod
    def setUpClass(cls):
        cls.TEST_MODEL = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.TEST_MODEL)

    def setUp(self):
        self.model = Model()

    def test_add_artists(self):
        artist_factors = numpy.random.rand(4, Model.FACTORS) * 0.2 - 0.1
        self.model.add_artists(
            artist_factors, ["dEUS", "Spinal Tap", "Josie and the Pussycats", "Anvil"]
        )
        self.assertIsNotNone(self.model.playlist_model)
        self.assertIsNone(self.model.playlist_model.user_factors)
        self.assertIsNotNone(self.model.playlist_model.item_factors)
        self.assertTrue(self.model.artist_names)
        self.assertFalse(self.model.dirty_playlists)
        self.assertTrue(self.model.dirty_artists)

    def test_init(self):
        self.assertIsNotNone(self.model.playlist_model)
        self.assertIsNone(self.model.playlist_model.user_factors)
        self.assertIsNone(self.model.playlist_model.item_factors)
        self.assertFalse(self.model.artist_names)
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_fit(self):
        PLAYS = 50
        plays = scipy.sparse.csr_matrix(
            (
                numpy.random.randint(1, 10, size=PLAYLISTS * PLAYS),
                (
                    numpy.random.randint(0, ARTISTS, size=PLAYLISTS * PLAYS),
                    list(range(PLAYLISTS)) * PLAYS,
                ),
            ),
            shape=(ARTISTS, PLAYLISTS),
        )
        artists = [str(a) for a in range(ARTISTS)]
        playlists = [str(a) for a in range(PLAYLISTS)]
        self.model.fit(plays, playlists, artists)
        self.assertTrue(self.model.dirty_playlists)
        self.assertTrue(self.model.dirty_artists)
        self.assertEqual(ARTISTS, len(self.model.artist_names))
        self.assertEqual(ARTISTS, len(self.model.artist_by_name))
        self.assertEqual(PLAYLISTS, len(self.model.playlist_ids))

    def test_load(self):
        self.model.load(folder=self.TEST_MODEL)
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    # @unittest.skip("slow")
    def test_load_big(self):
        self.model.load()
        self.assertIsNotNone(self.model.playlist_model)
        self.assertIsNotNone(self.model.playlist_model.user_factors)
        self.assertIsNotNone(self.model.playlist_model.item_factors)
        # self.assertTrue(self.model.playlist_ids)
        self.assertTrue(self.model.artist_names)
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_fit_then_save(self):
        self.test_fit()
        self.model.save(folder=self.TEST_MODEL)
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_save_dir(self):
        self.test_add_artists()
        self.test_add_playlist()
        with tempfile.TemporaryDirectory() as tmp:
            self.model.save(folder=tmp)
            self.assertFalse(self.model.dirty_playlists)
            self.assertFalse(self.model.dirty_artists)

    def test_save_async_dir(self):
        self.test_add_artists()
        self.test_add_playlist()
        with tempfile.TemporaryDirectory() as tmp:
            self.model.save_async(folder=tmp)
            self.assertFalse(self.model.dirty_playlists)
            self.assertFalse(self.model.dirty_artists)

    def test_add_playlist(self):
        playlist_factors = numpy.random.rand(Model.FACTORS)
        no = self.model.add_playlist(playlist_factors, "test_add_playlist")
        self.assertEqual(no, 0)
        self.assertTrue(self.model.dirty_playlists)
        no = self.model.add_playlist(playlist_factors, "test_add_playlist2")
        self.assertEqual(no, 1)
        self.assertTrue(self.model.dirty_playlists)

    def test_process_playlist(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_playlist([{"artists": ["1"]}], "test_process_playlist")
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_playlist_no_id(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_playlist([{"artists": ["1"]}], None)
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_playlist_with_unknown(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_playlist(
            [{"artists": ["1", "nonexistentartist"]}],
            "test_process_playlist_with_unknown",
        )
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(["2"], "test_process_artists")
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_no_id(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(["2"], None)
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_twice(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(["1"], "2")
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_filter_known(self):
        self.test_process_artists()
        res = self.model.process_artists(["2"], "test_process_artists")
        self.assertNotIn("test_process_artists", res["playlists"])

    def test_process_artists_ignore_case(self):
        self.test_process_artists()
        res = self.model.process_artists(["2"], "TEST_PROCESS_ARTISTS")
        self.assertNotIn("test_process_artists", res["playlists"])

    def test_process_artists_no_update(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(
            ["1"], "test_process_artists_no_update", update=False
        )
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_no_recommend(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(
            ["1"], "test_process_artists_no_recommend", recommend=False
        )
        self.assertFalse(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_no_update_recommend(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(
            ["1"],
            "test_process_artists_no_update_recommend",
            update=False,
            recommend=False,
        )
        self.assertFalse(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_process_artists_unknown(self):
        res = self.model.process_artists(
            ["nonexistentartist"], "test_process_artists_unknown"
        )
        self.assertDictEqual(res, {})
        self.assertFalse(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_reset(self):
        self.model.reset()
        self.assertListEqual(self.model.playlist_ids, [])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)

    def test_load_then_process(self):
        self.model.load(folder=self.TEST_MODEL)
        res = self.model.process_artists(["1"], "test_load_then_process")
        self.assertTrue(res["artists"])
        self.assertTrue(res["playlists"])
        self.assertTrue(self.model.dirty_playlists)
        self.assertFalse(self.model.dirty_artists)
