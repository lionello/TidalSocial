import { assert } from "chai"
import { describe } from "mocha"
import { processPlaylist } from "../src/model"

describe("model", function () {
  it("processPlaylist", async function () {
    const playlist = await processPlaylist(
      {
        tracks: [{ trackName: "Creep", artists: ["Radiohead"] }],
        url: "https://tidal.com/blah",
      },
      { update: false }
    )
    assert.isNotEmpty(playlist.artists)
    assert.isNotEmpty(playlist.playlists)
  })
})
