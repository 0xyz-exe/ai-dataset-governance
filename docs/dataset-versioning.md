# Dataset Versioning & Content Addressing

## Immutability Guarantee

Once a version is committed, its manifest is locked. The manifest contains the deterministic SHA-256 hash of all sorted member files and their corresponding blob digests.

```json
{
  "dataset_id": "ds_8195414f67e0",
  "version_num": 1,
  "semver": "v1.0.0",
  "files": [
    {
      "path": "labels/frame_0001.txt",
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 320
    }
  ]
}
```

The SHA-256 digest of this canonical JSON representation becomes the `manifest_hash`. Any alteration in file contents, addition of files, or deletion of files results in a different manifest hash.

## Differential Version Comparison

When comparing two versions (Base vs Target), the engine classifies files into:
1. **Added Files**: Present in target snapshot, absent in base snapshot.
2. **Removed Files**: Present in base snapshot, absent in target snapshot.
3. **Modified Files**: Present in both snapshots with identical logical paths but diverging SHA-256 digests.
4. **Unchanged Files**: Byte-identical files preserved via reference deduplication.
