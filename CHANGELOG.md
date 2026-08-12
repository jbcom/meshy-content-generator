# Changelog

## [0.3.0](https://github.com/jbcom/meshy-content-generator/compare/meshy-content-generator-v0.2.0...meshy-content-generator-v0.3.0) (2026-08-12)


### Features

* allow credit-free asset reprocessing ([e72e73a](https://github.com/jbcom/meshy-content-generator/commit/e72e73a01909a67d1abc37e6094e232c829dde89))
* **brand:** Signal Amber rebrand — warm amber palette, custom typography, brand SVGs ([8fc661b](https://github.com/jbcom/meshy-content-generator/commit/8fc661b6352497a3fbba46d83983a66167604aa5))
* complete CI/CD overhaul, autodoc pipeline, and SonarCloud integration ([685e5e7](https://github.com/jbcom/meshy-content-generator/commit/685e5e75966ce90b156189a66c1245ebc8118e34))
* launch readiness sweep — tests, docs, workflows, OIDC ([#75](https://github.com/jbcom/meshy-content-generator/issues/75)) ([303a540](https://github.com/jbcom/meshy-content-generator/commit/303a540ee1c689d8534f50c073e14491cf806273))
* **monorepo:** add Nx project configs and polyglot CI workflow ([f778297](https://github.com/jbcom/meshy-content-generator/commit/f77829725489edd91405b09830fe8be9bb3f6226))
* **monorepo:** migrate all packages from org repos ([8cd4e2a](https://github.com/jbcom/meshy-content-generator/commit/8cd4e2a0da90718a0b9b17b67262d55591f0e6ae))
* replace duplicate Meshy client with vendor-fabric pipeline ([b34b1d9](https://github.com/jbcom/meshy-content-generator/commit/b34b1d9372aba238c648b1396f0c2809e93b9e01))


### Bug Fixes

* **ci:** resolve all CI failures — TypeScript types, Python imports, Rust deps, E2E mobile ([2b1fc4d](https://github.com/jbcom/meshy-content-generator/commit/2b1fc4d2440ca5a3fd0a66eaaf28f2a4aca8c7f2))
* **ci:** resolve Biome lint failures across all TS packages ([1f7ee76](https://github.com/jbcom/meshy-content-generator/commit/1f7ee76fa531f0c6beb94c6dd66a298134d123b5))
* **deps:** remediate 153 open Dependabot alerts (4 critical, 55 high) ([#114](https://github.com/jbcom/meshy-content-generator/issues/114)) ([6023e0f](https://github.com/jbcom/meshy-content-generator/commit/6023e0f6258dda095ffc5bd843d5698d21eecf77))
* **meshy:** animation task responsePath — use 'result' not 'id' ([5a9effe](https://github.com/jbcom/meshy-content-generator/commit/5a9effec1989659f71a7f24df878a25d10c52812))
* **meshy:** resolve Scalar API reference type error ([43e7e90](https://github.com/jbcom/meshy-content-generator/commit/43e7e90c71b5f7c80110d55c9f0ed6ad7e0c2760))
* preserve transparency through backdrop processing ([85f1f5e](https://github.com/jbcom/meshy-content-generator/commit/85f1f5eab456cb285bae8a8ace7322b1e04e8706))
* require the vendor-fabric text-to-image release ([14a1e25](https://github.com/jbcom/meshy-content-generator/commit/14a1e2527b8f15f3cf446b85ac0a6df9caa5d542))
* resolve package name collisions, update org references, add SonarCloud and root README ([4930e13](https://github.com/jbcom/meshy-content-generator/commit/4930e13e592a7aad9dc810a54c9eef6beab693a0))


### Documentation

* comprehensive docs overhaul — API refs, READMEs, design, content ([496eb8f](https://github.com/jbcom/meshy-content-generator/commit/496eb8fe740c419cbd012ff9247aa60db88ecc99))

## [0.2.0](https://github.com/jbcom/meshy-content-generator/releases/tag/meshy-content-generator-v0.2.0) (2026-08-12)

### Features

* replace the duplicate Meshy client with a declarative pipeline backed exclusively by `vendor-fabric` ([b34b1d9](https://github.com/jbcom/meshy-content-generator/commit/b34b1d9372aba238c648b1396f0c2809e93b9e01))
* allow credit-free reprocessing of existing assets through changed manifests ([e72e73a](https://github.com/jbcom/meshy-content-generator/commit/e72e73a01909a67d1abc37e6094e232c829dde89))

### Bug Fixes

* require the released `vendor-fabric` text-to-image contract ([14a1e25](https://github.com/jbcom/meshy-content-generator/commit/14a1e2527b8f15f3cf446b85ac0a6df9caa5d542))
* preserve keyed transparency through feather, mat-removal and parallax masks ([85f1f5e](https://github.com/jbcom/meshy-content-generator/commit/85f1f5eab456cb285bae8a8ace7322b1e04e8706))
