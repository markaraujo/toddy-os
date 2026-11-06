#!/bin/bash
# Source from the future /init after mounting an ISO candidate read-only.
# Expected values come from generated initramfs data, never evaluated media text.
toddy_verify_media() {
 if [[ $# != 3 ]]; then
  printf 'Toddy media verification requires mount, identity and root digest\n' >&2
  return 1
 fi
 local media=$1 expected_id=$2 expected_sha=$3 observed_id checksum output
 if [[ ! $expected_id =~ ^[0-9a-f]{64}$ || ! $expected_sha =~ ^[0-9a-f]{64}$ ]]; then
  printf 'Invalid embedded Toddy media identity or root digest\n' >&2
  return 1
 fi
 if [[ ! -d $media || -L $media || ! -f $media/.toddy-media-id || -L $media/.toddy-media-id ||
       ! -d $media/live || -L $media/live || ! -f $media/live/rootfs.squashfs || -L $media/live/rootfs.squashfs ]]; then
  printf 'Toddy media is missing regular identity/root payload files\n' >&2
  return 1
 fi
 observed_id=$(cat -- "$media/.toddy-media-id") || return 1
 if [[ $observed_id != "$expected_id" ]]; then
  printf 'Toddy media identity does not match this initramfs\n' >&2
  return 1
 fi
 # Standard input avoids filename escaping in sha256sum's output. The path is
 # fixed and every media-controlled path component below its mount was checked.
 output=$(sha256sum < "$media/live/rootfs.squashfs") || return 1
 checksum=${output%% *}
 if [[ $checksum != "$expected_sha" ]]; then
  printf 'Toddy root image SHA-256 mismatch\n' >&2
  return 1
 fi
 return 0
}
