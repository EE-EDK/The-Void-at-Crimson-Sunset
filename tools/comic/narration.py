"""Build the per-shot narration index from the video-project shot map."""


def _beats_of(shot):
    seen, out = set(), []
    for b in shot.get("beats", []):
        name = b.split("/")[0]
        if name not in seen:
            seen.add(name); out.append(name)
    return out


def build_index(shots, available_shots, web_prefix):
    out_shots, beat_to_shot = [], {}
    for shot in shots:
        sid = shot["shot_id"]
        beats = _beats_of(shot)
        ready = sid in available_shots
        out_shots.append({
            "shot": sid,
            "beats": beats,
            "audio": f"{web_prefix}/{sid}.mp3" if ready else None,
            "status": "ready" if ready else "pending",
        })
        for b in beats:
            beat_to_shot[b] = sid
    return {"shots": out_shots, "beat_to_shot": beat_to_shot}
