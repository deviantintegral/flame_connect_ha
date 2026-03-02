# Changelog

## [0.1.1](https://github.com/deviantintegral/flame_connect_ha/compare/v0.1.0...v0.1.1) (2026-03-01)


### Documentation

* add initial quality scale eval ([3424656](https://github.com/deviantintegral/flame_connect_ha/commit/34246561a5236f42f5c0b239591d9282063a2f2e))

## 0.1.0 (2026-02-28)


### Features

* add AI task manager configuration and infrastructure ([dd5df81](https://github.com/deviantintegral/flame_connect_ha/commit/dd5df81c11240f0d2f3b50d5e0d3b2500d5941b3))
* add boost duration number entity and boost end sensor ([3e5e596](https://github.com/deviantintegral/flame_connect_ha/commit/3e5e596c25a6741727026eb206bb8113a08624a5))
* add coordinator, integration entry, repairs, and diagnostics ([b19f20a](https://github.com/deviantintegral/flame_connect_ha/commit/b19f20ac8c74955674d6bb6ac96b6e8babd74584))
* add FlameConnect HA integration plan ([ca1625d](https://github.com/deviantintegral/flame_connect_ha/commit/ca1625d8b784bc9e82fcef78313e390c25206a20))
* add MSAL token management module for FlameConnect auth ([6dee09a](https://github.com/deviantintegral/flame_connect_ha/commit/6dee09aca021d89d6ff19f59778e5fc97279ba1e))
* add release-please for automated releases ([#16](https://github.com/deviantintegral/flame_connect_ha/issues/16)) ([80055a7](https://github.com/deviantintegral/flame_connect_ha/commit/80055a71decf51ad43c667fb9d027c2a232ae253))
* add specific MDI icons to all entity descriptions ([88bbe3c](https://github.com/deviantintegral/flame_connect_ha/commit/88bbe3cb809aafac93bd615e367876b12c8b19db))
* add timer end timestamp sensor ([b3ffb28](https://github.com/deviantintegral/flame_connect_ha/commit/b3ffb28bde0c0f7615a9b8ab330c0996f2b46ec4))
* enable debug logging from flameconnect library ([992964d](https://github.com/deviantintegral/flame_connect_ha/commit/992964d3fd85b373ddbcddbe8737f40ad6be4e90))
* gate entity creation on FireFeatures flags ([eee476d](https://github.com/deviantintegral/flame_connect_ha/commit/eee476d0a107c104c3a250019333857c82cd9b21))
* implement all 7 entity platforms ([86a7a7c](https://github.com/deviantintegral/flame_connect_ha/commit/86a7a7ce698d0ba11c2dc1e3552f2b904bf7436b))
* initialize integration as FlameConnect with domain flameconnect ([bfacb5e](https://github.com/deviantintegral/flame_connect_ha/commit/bfacb5e30b2c5dbf95b17110933ff9fcc942d674))
* remove scaffold code and set up project infrastructure ([1d043af](https://github.com/deviantintegral/flame_connect_ha/commit/1d043af4b93c9b1ab440cc55e5690863960d6829))
* rewrite base entity for multi-device fireplace support ([2ce80cb](https://github.com/deviantintegral/flame_connect_ha/commit/2ce80cb85a573ca4153ff3246f735c7e1e70c051))
* rewrite config flow for Azure AD B2C authentication ([2f997ad](https://github.com/deviantintegral/flame_connect_ha/commit/2f997ad9651c001bdd0636b62c01d174cb95377c))
* rewrite translations for FlameConnect entities and config flow ([09f887d](https://github.com/deviantintegral/flame_connect_ha/commit/09f887ddae1a5a202e60ff632c4b6ff16eb48e1c))
* schedule coordinator refresh 60s after timer expiry ([99fcb0a](https://github.com/deviantintegral/flame_connect_ha/commit/99fcb0a84f163f7ffda0be7cf435bcb4829930ed))
* upgrade flameconnect to 0.4.0 and log feature flags ([60ed3e6](https://github.com/deviantintegral/flame_connect_ha/commit/60ed3e6fb09063ab8c558e70d75a9a32cdb2290d))
* write timer duration to API immediately when timer is running ([33cbb4c](https://github.com/deviantintegral/flame_connect_ha/commit/33cbb4cdd05f8d47014d9d6a371c2f8653243e64))


### Bug Fixes

* absorb pending debounced writes into immediate writes ([593ac79](https://github.com/deviantintegral/flame_connect_ha/commit/593ac79cec61958509e7a036fac1a9c8194ac13b))
* async coroutine return in setup ([7cfb3bc](https://github.com/deviantintegral/flame_connect_ha/commit/7cfb3bc65416df4a83d3bc14c1e61bd67431b2aa))
* defer timer/boost end sensor init until hass is available ([4e602db](https://github.com/deviantintegral/flame_connect_ha/commit/4e602db58cdd7b3d870e6cc8887f4db564d72f9b))
* pythonpaths for imports ([37abdc1](https://github.com/deviantintegral/flame_connect_ha/commit/37abdc1507af7da7d638d0ef091689d00d36b98a))
* replace remaining jpawlowski references in README.md ([59cb7b6](https://github.com/deviantintegral/flame_connect_ha/commit/59cb7b66238d91806a039d69c782eb76f8866408))
* resolve hassfest CI validation errors ([#7](https://github.com/deviantintegral/flame_connect_ha/issues/7)) ([adfa26f](https://github.com/deviantintegral/flame_connect_ha/commit/adfa26f3f8571e92f39533089112cd9f2534d8bc))
* resolve ruff import sorting errors in handler.py and base.py ([017bcf8](https://github.com/deviantintegral/flame_connect_ha/commit/017bcf85d5c89ac0de43f7130d14b852bc2d4409))
* revert default_name and detect heat from overview parameters ([0231a8e](https://github.com/deviantintegral/flame_connect_ha/commit/0231a8e410b8452f278783c19859547c1a340855))
* show timer end sensor as unavailable when timer is off ([32a2730](https://github.com/deviantintegral/flame_connect_ha/commit/32a2730d8a8ddc10d75c3ee680d176751b7e3eb8))
* sort manifest.json keys per hassfest requirements ([#17](https://github.com/deviantintegral/flame_connect_ha/issues/17)) ([897f627](https://github.com/deviantintegral/flame_connect_ha/commit/897f62720168497d3ad882bc28cbf4cfa87c2cbd))
* store timer duration locally instead of writing to API ([1cde429](https://github.com/deviantintegral/flame_connect_ha/commit/1cde429000fe21254dcf05604634b1cf2c21a6a8))
* timer switch sends both status and duration matching TUI behavior ([d9d202b](https://github.com/deviantintegral/flame_connect_ha/commit/d9d202bbed0b7a326b79bfe7231ba0d03ad3c87f))
* use AsyncMock for b2c_login_with_credentials in config flow tests ([c2a6721](https://github.com/deviantintegral/flame_connect_ha/commit/c2a6721313f91413bfeba5a1ebd3aead947cd8fa))
* use default_name for device info to allow user customization ([ae4780a](https://github.com/deviantintegral/flame_connect_ha/commit/ae4780a4bdfa56fdb411d03719535c0bff5f9f23))


### Documentation

* generate initial integration tasks ([8fe714b](https://github.com/deviantintegral/flame_connect_ha/commit/8fe714bffc534cc3b2903502f7a968a6d479b50f))
* rewrite README and AGENTS.md for FlameConnect integration ([498d52a](https://github.com/deviantintegral/flame_connect_ha/commit/498d52a1005a999013e27b0ebbc08b73eaace086))
* update AGENTS.md for flameconnect 0.4.0 and feature-gated entities ([90c648d](https://github.com/deviantintegral/flame_connect_ha/commit/90c648de74443674d114b32896f542e2b7e79070))
