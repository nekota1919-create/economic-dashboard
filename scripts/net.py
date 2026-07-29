"""HTTPS通信の共通セットアップ。

一部のWindows環境ではセキュリティソフト等のTLSインスペクションにより、
Python標準/certifiの証明書検証や、yfinanceが使うcurl_cffi(libcurl)の
証明書検証が失敗することがある。
ここでWindowsの証明書ストア(ROOT/CA)を読み取り、certifiのバンドルに
追記した組み合わせCA束を生成してキャッシュし、`SSL_CERT_FILE` /
`CURL_CA_BUNDLE` 環境変数で全ライブラリに使わせる。
GitHub Actions(Linux)など証明書問題が無い環境では何もしない。
"""
from __future__ import annotations

import base64
import os
import pathlib
import platform
import ssl

import certifi


def _ensure_windows_ca_bundle() -> None:
    if platform.system() != "Windows":
        return
    if os.environ.get("CURL_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE"):
        return

    cache_dir = pathlib.Path(__file__).parent / ".cache"
    cache_dir.mkdir(exist_ok=True)
    bundle_path = cache_dir / "combined_ca_bundle.pem"

    if not bundle_path.exists():
        parts = [pathlib.Path(certifi.where()).read_text(encoding="utf-8")]
        for store in ("ROOT", "CA"):
            for der_bytes, encoding, _trust in ssl.enum_certificates(store):
                if encoding != "x509_asn":
                    continue
                b64 = base64.b64encode(der_bytes).decode("ascii")
                wrapped = "\n".join(b64[i : i + 64] for i in range(0, len(b64), 64))
                parts.append(f"-----BEGIN CERTIFICATE-----\n{wrapped}\n-----END CERTIFICATE-----\n")
        bundle_path.write_text("\n".join(parts), encoding="utf-8")

    os.environ["CURL_CA_BUNDLE"] = str(bundle_path)
    os.environ["SSL_CERT_FILE"] = str(bundle_path)


_ensure_windows_ca_bundle()

import truststore  # noqa: E402

truststore.inject_into_ssl()
