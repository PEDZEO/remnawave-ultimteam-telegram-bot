# Changelog

## [3.26.0](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/compare/v3.25.1...v3.26.0) (2026-07-08)


### New Features

* add admin balancer endpoints for cabinet ([ff2f721](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ff2f7212160197661d2fac495bb56a79bb13958a))
* add admin sales statistics API with 6 analytics endpoints ([69c5323](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/69c5323e1be0b001c4dd286d64f66084de382e2c))
* add ChatTypeFilterMiddleware to ignore group/forum messages ([c9b4247](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c9b4247af2c37f8ed6cab58ed797363b4d925242))
* add ChatTypeFilterMiddleware to ignore group/forum messages ([25f014f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/25f014fd8988b5513fba8fec4483981384687e96))
* add CLASSIC_PERIOD_PRICES to config ([ad79130](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ad7913078b823f5b2dcfc0e865f7fcfb0dbe7363))
* add daily deposits by payment method breakdown ([c338977](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c338977ba52469108200166774ae64e92de8d15a))
* add daily device purchases chart to addons stats ([4388d3b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4388d3b297a87bae2fe647ce9f8d65159acc6e70))
* add dedicated sales_stats RBAC permission section ([e642475](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e642475bb8c697961f8d160671feb68c4651219c))
* add desired commission percent to partner application ([6016128](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6016128630221c69ec77a41508985b4f12c0a7a6))
* add gifts section to admin user detail API ([e0561f0](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e0561f08f0378d192b6adf294df37089f98ffb6f))
* add granular user permissions (balance, subscription, promo_group, referral, send_offer) ([60c4fe2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/60c4fe2e239d8fef7726cac769711c8fcce789eb))
* add LIMITED subscription status and preserve extra devices on tariff switch ([06dd0f8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/06dd0f8a49fa281f5ee2ab0fc20ae04331c85cca))
* add managed news categories and tags with DB-backed CRUD ([bd2e085](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bd2e08590a47b211cbd4313ae81955522d07ef08))
* add media upload/delete API for news articles ([0cfdc38](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0cfdc3882bbb43a2081d5146fa79fb120d90d902))
* add multi-channel mandatory subscription system ([0420237](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/04202379dbd0eb357323b77c518d2d891d52cbce))
* add multi-channel mandatory subscription system ([8375d7e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8375d7ecc5e54ea935a00175dd26f667eab95346))
* add news articles module with admin CRUD and public API ([c1c0423](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c1c04234eca837b1bc9a81f5f68c1148e974c646))
* add per-channel disable settings and fix CHANNEL_REQUIRED_FOR_ALL bug ([3642462](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3642462670c876052aa668c1515af8c04234cb34))
* add promo group and promo offer discounts to gift subscriptions ([4ab64fb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4ab64fb241902cfbc44c766d03b5fbc585208f08))
* add RBAC + ABAC permission system for admin cabinet ([3fee54f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3fee54f657dc6e0db1ec36697850ada2235e6968))
* add RenewalPricing dataclass and PricingEngine discount methods ([0a24db7](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0a24db7bb94258db127b51ee5a4d115685b1f7d8))
* add required channels button to admin settings submenu in bot ([4944568](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/494456837692cb3bf6645b0912c6d253a1147833))
* add required channels button to admin settings submenu in bot ([3af07ff](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3af07ff627fc354da4f8c41b0bd0575dddd9afa5))
* add RESET_TRAFFIC_ON_TARIFF_SWITCH admin setting ([2d1bc4e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2d1bc4e15451f619536b82347f8ad4aa30970fbc))
* add resource_type and request body to audit log entries ([388fc7e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/388fc7ee67f5fc0edf6b7b64b977e12a2d8f0566))
* add separate Freekassa SBP and card payment methods ([0da0c55](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0da0c5547d0648a70f848fe77c13d583f4868a52))
* add show_in_gift toggle for tariffs in admin panel ([74258b2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/74258b245193acf64a2954dac730848a218186eb))
* add sync-squads endpoint for bulk updating subscription squads in Remnawave ([dabd1f1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dabd1f1cc9b864160954087b382ee1f3228ef2f7))
* add ultima provider account linking mode ([9fe7998](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9fe7998d4aa43febfadc366512476c9d1c35f937))
* add ultima theme presets ([754af78](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/754af78dfcb34088da1607f230697cc915b5fb1a))
* add validation to animation config API ([a15403b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a15403b8b6e1ec1bb5c37fdde646e7790373e860))
* allow editing system roles ([f6b6e22](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f6b6e22a9528dc05b7fbfa80b63051a75c8e73cd))
* **api:** expose email field in UserResponse ([6fcc20f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6fcc20f4358c754f50497fc69356285accc7c140))
* auto-sync squads to Remnawave when admin updates tariff ([e1ee6bf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e1ee6bf911d7adbc6d1de68f2fbf69f5adbd275e))
* brand admin alerts for PEDZEO fork ([cec8257](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/cec82571866fbf6667395c024d8cf109b67e1efc))
* **branding:** add ultima theme config api ([c316189](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c3161895b0b027312bf373e9c6a40d8c6202deb1))
* **branding:** support ultima framesEnabled in theme config ([f96b61d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f96b61dc70ff7e5bd51695c198369d3531d49b87))
* **branding:** support Ultima home logo toggle in theme config ([61b21e3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/61b21e30a03ea017593904ac946071d97e7e1d13))
* **cabinet:** add default subscription payment method flag and tariff max devices ([f7976c9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f7976c9479c020946010395c66d9803930ded8aa))
* **cabinet:** add menu layout stats endpoints ([4ea3c5f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4ea3c5f87e4562f40eb20bb7361f72e201953025))
* **cabinet:** add ultima mode branding endpoints ([42e1b3d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/42e1b3dce553a29bc71c751b85aaed43d3e1fc8d))
* **cabinet:** proxy balancer quarantine admin endpoints ([9f67e21](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9f67e2127557b85c31e51589ee8bba0b9fa40de8))
* **cabinet:** support device_limit in tariff purchase pricing and activation ([38932d9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/38932d9cb637426490dd24ad20b5168eb0e021ca))
* capture query params in audit log details for all requests ([bea9da9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bea9da96d44965fcee5e2eba448960443152d4ea))
* colored channel subscription buttons via Bot API 9.4 style ([343bfcd](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/343bfcd18435803cd17eeef4be0ebdb584dfa102))
* colored channel subscription buttons via Bot API 9.4 style ([0b3b2e5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0b3b2e5dc54d8b6b3ede883d5c0f5b91791b7b9b))
* enforce single featured news article — unfeature others on toggle/create/update ([f222b4b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f222b4bf4d041d9046150a23e08674c9e2cfa86c))
* enhance sales stats with device purchases, per-tariff daily breakdown, and registration tracking ([732409c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/732409cc76719b82924f49fde849693d70d63d43))
* expose MULTI_TARIFF_ENABLED and MAX_ACTIVE_SUBSCRIPTIONS in admin settings ([ccb311f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ccb311f262cd4fcacab99a4f464173e18ff0c94b))
* **gift:** allow extending gifts with selected period ([b8b8186](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b8b81865f1837220443c21a25dffe06d04dc9c9a))
* **gift:** sync upstream gift subscription backend flows ([83c4d10](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/83c4d1036b6150f1c73941c942574f7acf51448e))
* **promocode:** return gift sender in activation response ([1c59e31](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1c59e318b5342baec5a0a4b90f495680473bddb5))
* proxy balancer groups management endpoints ([2ff2a3f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2ff2a3f63561a0a8c784c322b6653ba798543aa4))
* referral links now point to web cabinet instead of bot ([b4cd176](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b4cd176b04667e462fe0dc4ca31e67573b82566e))
* replace pip with uv in Dockerfile ([9031ab2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9031ab253e5292988effa96d2a6f1345dd11f0da))
* return detailed insufficient balance for gift extension ([ae14fa3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ae14fa388c3fb84cdf5114a9674a8daea95d3376))
* rework guide mode with Remnawave API integration ([5a269b2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5a269b249e8e6cad266822095676937481613f5f))
* support extending existing gift tokens ([b6d15ee](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b6d15eecba559fc9b2283813d7a8a346d883d34a))
* **tickets:** add user endpoint to close own ticket ([b68d0cb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b68d0cb375301502bf039b6877ac5251146b2e6d))
* **ultima:** add configurable notification buttons for bot alerts ([c0e3875](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c0e38756f07eac034929eea8ef0e2b9d46bfe25c))
* **ultima:** add standalone agreement endpoints for user and admin ([cec96e6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/cec96e6d7283b3c0f1e2b12bafe4e2ac673b7cbd))
* **ultima:** separate start flow with configurable app message ([7da6101](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7da6101012a7f4f6db47e5e3f3fdb5977f5a838d))
* **ultima:** support gift promo flow with partial top-up ([f4ffc98](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f4ffc98f50e3a3c18ebaa417bcb3c5951f824328))


### Bug Fixes

* abs() for transaction amounts in admin notifications and subscription events ([630a018](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/630a01845ec2f8bafddb6a6e0bf2fa3e59e28d53))
* adapt user FK ondelete migration for fork graph ([4df5b43](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4df5b435906b1153c8ec0b865d9e319fbe6d1279))
* add abs() to expenses query, display flip, contest stats, and recent payments ([e917b76](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e917b7667af52f5215f9ab58ad377d9de2f82ec9))
* add blocked user support button in bot ([e99f6e5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e99f6e581bfad161d5096e9fa42905a74bd82250))
* add classic waves animation preset ([a8378dd](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a8378dd3b5c7811651da4fc948f914cb1f54b50f))
* add diagnostic logging for device_limit sync to RemnaWave ([b6b91fb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b6b91fb3b8a736cd59bb488fba9fd4d0827954d8))
* add diagnostic logging for device_limit sync to RemnaWave ([97b3f89](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/97b3f899d12c4bf32b6229a3b595f1b9ad611096))
* add exc_info traceback to sync user error log ([427b53a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/427b53a47f9132df6901bf381150e4b3aa53ee7f))
* add int32 overflow guards and strengthen auth validation ([50a931e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/50a931ec363d1842126b90098f93c6cae47a9fac))
* add local traffic_used_gb reset in all tariff switch handlers ([2727635](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/27276350d964a7b443e58f80c9aebd6cac749845))
* add min_length to state field, use exc_info for referral warning ([35c6add](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/35c6add59b6a746720bb61eaeb4b180e7d170948))
* add missing broadcast_history columns and harden subscription logic ([d4c4a8a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d4c4a8a211eaf836024f8d9dcb725f25f514f05e))
* add missing CHANNEL_CHECK_NOT_SUBSCRIBED localization key ([66644de](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/66644defdf98e263537c0ab05f070dff957970b1))
* add missing CHANNEL_CHECK_NOT_SUBSCRIBED localization key ([a47ef67](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a47ef67090c4e48f466286f7c676eeee0c61a4fb))
* add missing mark_as_paid_subscription, fix operation order, remove dead code ([78caaf5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/78caaf560b6de3bd28082d655962da296d2e86ee))
* add missing settings import in admin_users tariff switch ([b849ad1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b849ad1594c71476bf7c1d3e738b44198230757d))
* add missing subscription columns migration ([7075e0e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7075e0e99ef59875143e01f8d8c6785041dcfbb1))
* add nested selectinload and referrer eager loading to prevent MissingGreenlet ([9d80077](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9d8007788a7d82fe1f8c182a5b2c3638c05ed12a))
* add NoScriptError import fallback for redis test stubs ([39c6f8c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/39c6f8c4550de6cda0809b878be570ecb5673e04))
* add per-category discounts and months multiplier to classic mode ([254a412](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/254a412978082e16a5198b786cf5dbeacf8cc836))
* add period_days whitelist validation and type annotations ([3c35022](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3c35022cd5104c2eb5e459a2baeac81962c16edf))
* add post_update=True to User.referrals self-referential relationship ([5d52d24](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5d52d24dbe52155e27c2b0325b45d2edbff31637))
* add selectinload to user lock queries to prevent MissingGreenlet ([529c3f1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/529c3f1ccd21456d895a3320b82c77f77ae0e3c8))
* add Telegram Stars payment support for gift subscriptions ([dfdec12](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dfdec12cc2a52b47863dae72c34a3367f38332a3))
* address code review issues in guide mode rework ([fae6f71](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fae6f71def421e319733e4edcf1ca80a2831b2ec))
* address RBAC review findings (CRITICAL + HIGH) ([1646f04](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1646f04bde47a08f3fd782b7831d40760bd1ba60))
* address review findings from agent verification ([370208e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/370208ef4eab906a30047b04061e22db68a5af58))
* address security review findings ([6feec1e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6feec1eaa847644ba3402763a2ffefd8f770cc01))
* align guest purchase service with fork architecture ([7241663](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7241663f5419843bb865d7082d074147b4ee1c88))
* align migration tests with alembic heads target ([521f866](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/521f866e83d8371a2098a8a69bdf295bec3c3000))
* align RBAC route prefixes with frontend API paths ([5a7dd3f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5a7dd3f16408f3497a9765e79a540ccdabc50e69))
* allow tariff switch when less than 1 day remains ([167919d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/167919d0aa4d87e9211310a70f799f550d2e5024))
* allow tariff switch when less than 1 day remains ([67f3547](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/67f3547ae2f40153229d71c1abe7e1213466e5c3))
* always include details in successful audit log entries ([3dc0b93](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3dc0b93bdfc85fb97f371dc34e024272766afc65))
* append cache buster to generated miniapp urls ([c869559](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c8695597575f640535d21aed95e575b404e68bfd))
* atomicity refactor, review fixes, and DELETED recovery logging ([dc86d18](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dc86d188fb84a81754de5eb61b4707c0ea7cfbe0))
* **auth:** make refresh JWT unique with jti ([38f9f6c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/38f9f6c190bab01d9f4e20f17f2e5775884347ca))
* **auth:** restore optional telegram identity validation ([38a7029](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/38a7029e044c1486ba62da54a39af94b3f43eb97))
* auto-update permissions for system roles on bootstrap ([d8f07b8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d8f07b8caf9d38efdfcc93da37088442aad18be9))
* avoid button click FK race on user lookup ([1f814a6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1f814a6cff2031a2ce788a6c9b2aded4e9d1d655))
* avoid invalid ultima notification webapp buttons without miniapp url ([11299da](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/11299da0ea6a3797979d0b4692da31f889464cf9))
* avoid locale writability warning when no template sync is needed ([53323ae](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/53323aeb0aeca4919ddc96e12ffaa3600d9cb9e2))
* **backup:** add missing settings app config path getter ([0d6c670](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0d6c67092614da4e8f2d04e63307e0b60b6e5ded))
* **bot:** harden user and notification flows ([d480af6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d480af682224b834b04e51cd551106726d239654))
* **build:** refresh uv lock for release 3.24.0 ([6f0cd89](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6f0cd89101df5d2e514b22d7808a921a6e8f9587))
* **build:** refresh uv lock for release 3.24.1 ([60a8b64](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/60a8b64592526429488888c028a1012ce304290d))
* **cabinet:** add menu layout reset endpoint ([f5da309](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f5da30989e0a547b77720a0eff481525c47e004d))
* **cabinet:** sort route imports for ruff ([04cd4cf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/04cd4cf51f929bcf01884f487626794d85641127))
* **cabinet:** switch balancer proxy to admin endpoint namespace ([4544910](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/454491056cde3af1a67520ae6a089df6a9ab84e2))
* callback routing safety and cache invalidation order ([6a50013](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6a50013c21de199df0ba0dab3600b693548b6c1e))
* cap expected_monthly_referrals to prevent int32 overflow ([3173905](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3173905bd1da9caf1955e936d75d4709b4971cd0))
* cap expected_monthly_referrals to prevent int32 overflow ([2ef6185](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2ef618571570edb6011a365af8aa9cd7e3348c2e))
* centralize balance deduction and fix unchecked return values ([a527b8c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a527b8c4a5a45c8d193c8c93c1654c17a91f5581))
* centralize has_had_paid_subscription into subtract_user_balance ([7ff135c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7ff135c5dfd2f7da87bb69fe0e2302ba0a512f0c))
* change None assignment to [] + add "or []" guards at all 5 call sites. ([e1886c5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e1886c57404ea902ea2e333320327add41750e39))
* **ci:** make mypy checks pass locally and in workflow ([96d9116](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/96d9116ee466e2827a3ccdd8e1e68680b972d3bd))
* **ci:** sync uv lock for 3.24.2 and harden release lock workflow ([2c618a7](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2c618a7687048b4733c34f2dc64243c0f373b739))
* complete FK migration — add 27 missing constraints, fix broadcast_history nullable ([1a5def2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1a5def29d8dbc9c59c92ceca38695a54cf67e975))
* consume promo offer on tariff balance flows ([c868149](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c86814951a3569332de61e8d50d6f33f6753df66))
* correct broadcast button deep-links for cabinet mode ([9ff3929](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9ff3929f1092948af0f55dd2faecfb4acd9070af))
* correct broadcast button deep-links for cabinet mode ([e5fa45f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e5fa45f74f969b84f9f1388f8d4888d22c46d7e8))
* correct cart notification after balance top-up ([3c2746e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3c2746e5e87eb4f10d59e7dec0a5b7ac13b28c9f))
* correct referral withdrawal balance formula and commission transaction type ([d8a372d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d8a372dc6b5e4ad4ed5e19fce6ad76243e6cadaf))
* correct skipped_count in sync-squads circuit breaker and simplify ternary ([475bf6f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/475bf6f490e630e6fa6172c461b414115872551a))
* count sales from completed payment transactions instead of subscription created_at ([e8861bf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e8861bf1899f0a64accd8e6e4580926a2049a16b))
* cross-validate Telegram identity on every authenticated request ([ff8ca98](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ff8ca98e32950a0165c1e1df8ba70449a3b830eb))
* cross-validate Telegram identity on every authenticated request ([973b3d3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/973b3d3d3ff80376c0fd19c531d7aac3ae751df8))
* **db:** repair missing tariff external squad column ([e230a3f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e230a3f1a3cca2d96a8951860ee77fedd4feb0ab))
* define UUID pattern in tariff schemas for external squad ([45ee3f2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/45ee3f2b23008d8ae92eba7d4507f854b27bbdf8))
* device_limit fallback 1→0 для корректного отображения безлимита ([8581fec](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8581fec02ef937ff74f65b0be1aee61c12879173))
* disable post-topup cart flow to avoid duplicate notifications ([dc6d360](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dc6d36010fb3666a94baf3696902fdc2fe656c0a))
* disable topup cart notifications only in ultima mode ([bcc2adc](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bcc2adc6cdd037e5d3f1ba4fce56d96102e1dbeb))
* downgrade known-harmless RemnaWave 400s to warning level ([2a2ddf5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2a2ddf57fbb6079a5f5e7c4be30c72d4c1bc67c5))
* eliminate double panel API call on tariff change, harden cart notification ([0937d62](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0937d62bf32cc7ceb25c2eb435fbb443b8b94f98))
* eliminate referral system inconsistencies ([0940897](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/09408976e7e49498e0a26b15f1acfee57df49849))
* email verification bypass, ban-notifications size limit, referral balance API ([aeda809](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/aeda80932162d17edd9a4cd14109f1edceeb1d07))
* enforce user restrictions in cabinet API and fix poll history crash ([fb76cbb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fb76cbbde4f2c15f4e1becfb2a4a871d34f270a7))
* ensure admin gift notifications for purchase and activation ([f59d685](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f59d68555f72aeb43810267e82ae694a277cb96f))
* expose sales stats routes and align RBAC permission ([10780d6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/10780d6ef09e9448cc5527409254f4a36dde0f7d))
* extract real client IP from X-Forwarded-For/X-Real-IP headers ([af6686c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/af6686ccfae12876e867cdabe729d0c893bd85a1))
* fallback balance lock for mocked sessions ([06f8fa2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/06f8fa2e293d4600bcb6a56399245d484ab11639))
* fallback button click log to null user on FK conflict ([3982bd4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3982bd40b76074e86ebd3c467a2fccead2b32f9e))
* freekassa OP-SP-7 error and missing telegram notification ([dd306ae](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dd306ae6926e5532c9ea9fe067bf83d5c8bf7b47))
* generate missing crypto link on the fly and skip unresolved templates ([0bec636](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0bec63664646e1ed5f8f7ae0ab5fe95a9551cc6e))
* **gift:** enable gift flow automatically in ultima mode ([4b56687](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4b56687e4de482e81bc5d6eaad8d0e058f26cddc))
* **gift:** fallback to active tariffs when show_in_gift is not configured ([2baa1c9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2baa1c97d9b1929d44c00e603c46943d5f336d7d))
* **gift:** prevent double activation and enforce delivered status ([3890d12](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3890d12ef85c241bad75a3f8074bde2b759ba60a))
* **gift:** reject reused gift promo and stack gift days ([e51a070](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e51a07030212c180179273361a2b6a4caa1243ce))
* **gift:** respect gift toggle and restore settings import ([ed8352f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ed8352f3f21ce6aec687e2b7dd3c67121fa9fecc))
* **gift:** unify already-used promo error code ([dc1fa2e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dc1fa2eedb1d53c7e18aa1cb80ce24098ae9bfea))
* grant legacy config-based admins full RBAC access ([8893fc1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8893fc128e3d8927054f1df1647e896e780c69e7))
* guard rollback on commit flag, add flush to promo_offer_log ([59d99bd](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/59d99bdd42a99862ababeeb5e3397f44c03a9c4e))
* handle expired callback queries and harden middleware error handling ([df13ab1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/df13ab117526332ad77b5551e4b055491f15192d))
* handle expired ORM attributes in sync UUID mutation ([33bd6e4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/33bd6e42a03edad6cb184ca4a8d5a3a548631913))
* handle legacy telegram_id in YooKassa webhook recovery metadata ([5c3204e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5c3204e84727aad158e3170154ca21f00cc4e82e))
* handle NULL used_promocodes for migrated users ([f017f91](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f017f9173e19e6a08a25180d9dea483111ecc523))
* handle RemnaWave API errors in traffic aggregation ([4fc6aee](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4fc6aeeb5f9d09b2bf8951cffb40704bc56b2085))
* handle RemnaWave API errors in traffic aggregation ([ed4624c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ed4624c6649bdbc04bc850ef63e5c86e26a37ce4))
* harden admin subscription notifications delivery ([5a96a2e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5a96a2e15f051c3cdbd1e8f32c82a114405da1f0))
* harden FK migration lookup for missing constraints ([4240f01](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4240f01b399607dfff391d452c16ac27dba09de1))
* harden remnawave API error handling and YooKassa user cross-validation ([2156784](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/21567846a5581000ab80c3d9f4bf3e16376c08ad))
* harden YooKassa webhook recovery user lookup ([e7342b5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e7342b5495d47f7e7f98bdadaadebedf31d7db15))
* hide traffic topup button when tariff doesn't support it ([c92f7a5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c92f7a55e0cb814ec13e5a45f2a12759d8acfdb4))
* HTML-escape all externally-sourced text in guide messages ([711ec34](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/711ec344c646844401f355695a7e8c0d4fb401ee))
* improve campaign notifications and ticket media in admin topics ([a594a0f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a594a0f79f48227f75d6102b4586179102c4d344))
* improve deduplication log message wording in monitoring service ([e0412aa](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e0412aa80c0b8c3d59d9671a312009d72d6b76c8))
* improve deduplication log message wording in monitoring service ([2aead9a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2aead9a68b6bf274c8d1497c85f2ed4d4fc9c70b))
* include desired_commission_percent in admin notification ([56a0cf5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/56a0cf5cd7cc7c9ee9e6676a380797259af3763c))
* initialize logger in bot_configuration.py ([988d0e5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/988d0e5c2f27538135d757187a0b6770f078b1d9))
* invalid ISO date format in node usage stats API call ([93aedaf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/93aedaf277f745f15baf0bb4b1b14219a576a7a4))
* invalidate app config cache on local file saves ([978726a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/978726a7856cf56257c49491afe569fa8c395eac))
* keep payment lock flow compatible with mocked sessions ([e1ad616](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e1ad6162245e0b38f82f148a716e94daec5b8cfe))
* linearize alembic gift migration chain ([fc1b210](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fc1b2101d00039860f8a2607740e7f5b3eb4d70b))
* lock user row before button click stats insert ([818ac96](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/818ac960f612100236bf8a32ed0e277f30114064))
* log callback button stats without user FK dependency ([ee7be0f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ee7be0f7f1353fb78cb7a1cb8c6348bacc5eea67))
* make migrations 0010/0011 idempotent, escape HTML in crash notification ([fd6b6ea](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fd6b6eae49d70b6c09b49ae77c46c99ed532f8c1))
* **menu-layout:** allow unknown condition keys in schema ([64895d1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/64895d1d8a433e2f081dd0526966ca745d1c727e))
* **menu-layout:** keep buy button visible for active users in tariffs mode ([d7326f3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d7326f333440985b200a2b39e67c542f223f80d6))
* migrate all remaining naive timestamp columns to timestamptz ([708bb9e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/708bb9eec7ea4360b26709fb2a3f82dd139ed600))
* **migrations:** add 0037 compatibility placeholder revision ([c13e79d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c13e79df5f01ab21ad5e19cff53c62ab6401240a))
* **migrations:** bootstrap fresh databases at head ([11c87e1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/11c87e1f7ac827a00292abe9f06329edbe786eca))
* **migrations:** make 0019 gift migration idempotent ([8361467](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8361467ae2f6665507c3ad5b9dbbf24e38a1118f))
* **migrations:** make unique constraints idempotent for 0015 and 0017 ([fffc122](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fffc1223e82986969bd9ba120377c4ff94f10e2e))
* **migrations:** normalize overlapping alembic revisions ([d21729a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d21729aae2d063d835dca7b9f56e8663226d4dcc))
* **miniapp:** correct helper schema relative imports ([16682ef](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/16682ef809aaaf6a300c5b592a129ccada4af36f))
* **miniapp:** correct payment helper schema import path ([21c4242](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/21c4242cd22d159d3818913327022233bcc3054d))
* **miniapp:** correct renewal payment cryptobot helper import ([48e3871](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/48e3871cf8a52707c581daf7081c7e0cf788fc57))
* **miniapp:** restore test compatibility after helper split ([f202586](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f202586366224c6522172e27d613f09af41376a0))
* news module security hardening, perf optimizations, bug fixes ([7c3d006](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7c3d006090be8d13e65f0dadfe4811b31b65f754))
* **news:** adapt permissions and migrations for fork ([6c6bed3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6c6bed3a2143d2c69f2b7be743e04611e220cc3d))
* **news:** return relative media urls ([2f535a9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2f535a92e058857655bc676c6e08b4e31b6f1b34))
* **news:** serialize list queries on shared db session ([ec40c09](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ec40c09c7d3b84ff8e5d74bf6387b026838e4168))
* normalize remnawave mutable user statuses ([f439cef](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f439cef8c2778b357c3e12675c62a2a98edcc6a8))
* partner system — CRUD nullable fields, per-campaign stats, atomic unassign, diagnostic logging ([8494433](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/84944332b61f818542e6404090d37798438349ab))
* payment providers — lock_user_for_update + commit=False atomicity ([709e0a6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/709e0a6c6e2b21eaa51468e8bd259c44e29b01d7))
* persist ticket media replies ([b28a415](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b28a41552b4e66807220ac6b3747f26fadd9c506))
* platega webhook ID fallback for SBP and card payments ([8c53fb5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8c53fb5f9d1e00fc6b3d0a7044f8aefe937319a0))
* point update notifications to PEDZEO repo ([564b07a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/564b07a60e9647f0f321b4bf6f07f731a79485d3))
* pre-existing bugs found during review ([1bb939f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1bb939f63a360a687fafba26bc363024df0f6be0))
* preserve auto-purchase admin notify and lazy websocket imports ([4bd1f0c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4bd1f0c73f23c3e7a0de8b1da8663e38d1de3ff1))
* preserve purchased devices when admin changes user tariff ([6bef3f3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6bef3f39bb224ef76dd58b3280d83ebbc227eb11))
* prevent account takeover via auto_login_token, ensure promo group on all purchase paths ([ef6a129](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ef6a12911d2d3a6e54a7fc199421cad2347fd81c))
* prevent balance loss on auto-purchase for DISABLED subscriptions and fix WATA expiration ([8d70fa3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8d70fa383d9d4dd4aead10b6ab44239069a7ae78))
* prevent infinite reuse of first_purchase_only promo code discounts ([14bd19f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/14bd19f79568d695ccb1bfcd2a2e0c7e0d8fc256))
* prevent missed gift admin notifications in cabinet flows ([d9514f6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d9514f6abdfb21651b9c4122de9404dd8dbe8344))
* prevent partner self-referral via own campaign link ([3c6552f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3c6552fc92022d13a45e40db98fd91fb7b6be67c))
* prevent partner self-referral via own campaign link ([115c0c8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/115c0c84c0698591da75d7d3b8fbd8e0fc8541ea))
* prevent race condition expiring active daily subscriptions ([145f39d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/145f39d9b87fdaecab4fac6a34e98658c5ddb6af))
* prevent squad drop on admin subscription type change, require subscription for wheel spins ([5a7df48](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5a7df483f95b91a30bece4b9e1d71ffa70ed9b05))
* prevent sync from overwriting subscription URLs with empty strings ([14082e4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/14082e46de4fdbd8e75a163b22b47b35e8d73684))
* **promocode:** return stable gift reuse error ([614e1b0](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/614e1b0bcd08d9e6e5d10d151f23e016310adc57))
* protect active paid subscriptions from being disabled in RemnaWave ([1b6bbc7](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1b6bbc7131341b4afd739e4195f02aa956ead616))
* RBAC API response format fixes and audit log user info ([4598c27](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4598c2785a42773ee8be04ada1c00d14824e07e0))
* RBAC audit log action filter and legacy admin level ([c1da8a4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c1da8a4dba5d0c993d3e15b2866bdcfa09de1752))
* reactivate disabled subscriptions before traffic sync ([692f30b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/692f30b772b31d5ac0ac4d98fef9998a71e91e65))
* reactivate subscription after traffic top-up when status is EXPIRED ([4ab9f4b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4ab9f4b15e373882ca00e9e482695dc7178c7d9b))
* record transactions for free tariff switches and admin tariff changes ([ca028b8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ca028b831d1050e0b80ae9d669b5c2da3c247781))
* redis cache uses sync client due to import shadowing ([7f0dd1a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7f0dd1a1b5a80bdcfd72b5612ff4c4ebf1bb79f4))
* register categories/tags/media routers before news to avoid route conflict ([3a5e385](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3a5e3857bc5c6893905f25e17b4e1136e706d097))
* reject occupied direct identity links ([ffa2933](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ffa29331962531b9ecb7c5088122406dd104c7e5))
* reject promo codes for days when user has no subscription or trial ([7aec1e7](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7aec1e7355223f2610d109b7edbff50ef0512d60))
* remap squashed alembic revisions ([171abe5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/171abe5365433f4cdc6e8dd30c266169fafdc262))
* remove [@username](https://github.com/username) channel ID input, auto-prefix -100 for bare digits ([512010a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/512010a6c9d871aa9898d22e1e0ab8b41cedf9a7))
* remove [@username](https://github.com/username) channel ID input, auto-prefix -100 for bare digits ([a7db469](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a7db469fd7603e7d8dac3076f5d633da654a3a57))
* remove duplicate gift admin alerts from cabinet routes ([21fae07](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/21fae0757870fdcf146bf4cc3553577d2b510e31))
* remove gemini-effect and noise from allowed background types ([731eb24](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/731eb2436428d0e12f1e5ccdebc72cd74fd7c65e))
* remove premature tariff_id assignment in _apply_extension_updates ([fa6e1b4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fa6e1b4a219e1244348b9518851d336044b2247a))
* remove unused settings import in admin users route ([841d528](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/841d528e49023b4eb93d54881fdcb4e7cac14aea))
* renewals stats empty on all-time filter ([be29e1f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/be29e1f1349f31b124700e864e87a7d66ce77865))
* repair missing DB columns and make backup resilient to schema mismatches ([c20355b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c20355b06df13328f85cc5a6045b3e490419a30a))
* reset subscription for paid users, trial-to-paid tariff conversion, gift purchase MissingGreenlet ([abf2882](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/abf288232d383be202b0d0f8c96cbabdaabcebda))
* resolve alembic duplicate revision conflict for referral migration ([e33e942](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e33e942d154b59f5149165e07be48fc5929b604f))
* resolve GROUP BY mismatch for daily_by_tariff query ([de41378](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/de413784d89a70e9230968343ae11caf0a487079))
* resolve MissingGreenlet in switch_tariff endpoint ([f610df3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f610df3a997c411669b63f1d4d118070688d6ec0))
* resolve post-sync renewal response and typing issues ([931027e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/931027e0b8ad70395b1af579b92a41c38f4280dc))
* resolve post-sync typing and runtime issues in auto-purchase ([3fbc8fe](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3fbc8fec80f434e17b9547a22b81d58b14a605f2))
* resolve ruff lint errors (import sorting, unused variable) ([b2d7abf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b2d7abf5bd10a98fd7ad1da50b5072afc65a5b48))
* resolve sync 404 errors, user deletion FK constraint, and device limit not sent to RemnaWave ([1ce9174](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1ce91749aa12ffcefcf66bea714cea218739f3fe))
* restore miniapp payment status classification and stabilize auto-purchase tests ([7aa464f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7aa464f225ecdff614a197dc4d4f6f7feccd5cd6))
* restore panel user discovery on admin tariff change, localize cart reminder ([2ec1d30](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2ec1d309c2ae4dde0ca9631bf6fab2ff8b237cca))
* restore post-merge model imports and device limit handling ([7a98eed](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7a98eed275884a8766f11ea5e26d706d0bf98bac))
* restore RemnaWave config management endpoints ([6f473de](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6f473defef32a6d81cee55ef2cd397d536a784a7))
* restore settings import in gift config route ([59ceb71](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/59ceb711e3fde0764148d82c8ef76cc5e72f4dbe))
* restore subscription_url and crypto_link after panel sync ([26efb15](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/26efb157e476a18b036d09167628a295d7e4c10b))
* run alembic upgrade against all heads on startup ([fd789ae](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/fd789aee1cce7c3f17e795cc8ac2035255600b13))
* send gift admin alerts via generic notification channel ([186ead3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/186ead3f0ccf9c71698157e25c8806bb4caac988))
* separate base and purchased traffic in renewal pricing ([3211d98](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3211d98fdbfe75c0f6d7da63ac48d7565bcc57dd))
* **settings:** allow admin trial overrides over env ([e4cc0ed](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e4cc0ed582d550b323da3532c296e434d4902159))
* show negative amounts for withdrawals in admin transaction list ([21c3a01](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/21c3a016b3fdeac85d21cebbabe61188400be904))
* show negative amounts for withdrawals in admin transaction list ([5ee45f9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5ee45f97d179ce2d32b3f19eeb6fd01989a30ca7))
* show tariffs for legacy users without promo group ([aa1923f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/aa1923f391e117c7eb65367b565bb00a9d866cf3))
* silence optional locale sync warning on read-only mounts ([27831ef](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/27831efcebcfc0bcda1b4dc5d2aecad72c323805))
* silence PARTICIPANT_ID_INVALID error in channel subscription check ([4ef8599](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4ef8599a9c370e1e82c5082f733b4ea7e5824b0c))
* specify foreign_keys on User.admin_roles_rel to resolve ambiguous join ([bc7d061](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bc7d0612f1476f2fdb498cd76a9374b41fd9440a))
* stabilize backend ci imports ([7a4fb1f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7a4fb1f264767ceab206d66c77a449b3289e3798))
* stabilize upstream payment sync and webhook compatibility ([c25e772](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c25e77237ed19be7b092cf93c18302cee5c54a77))
* stack promo group + promo offer discounts in bot (matching cabinet) ([628997f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/628997fb48413cc4fae9ac491d1c7f6185877200))
* **subscription:** refresh stale remnawave links ([80c834a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/80c834a10cfff6fc58fee875f62b1ad6ece2ec14))
* support non-committing notification cleanup in subscription flow ([55a131c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/55a131c8c0dfa4e9faf0a306c5ae8c8910bbe026))
* suppress web page preview when logo mode is disabled ([edff3d8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/edff3d851735d4212e8fd807a542a9d0ee836180))
* suppress web page preview when logo mode is disabled ([1f4430f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1f4430f3af8f3efcc58ef7b562904adcb1640a44))
* sync traffic reset across all tariff switch code paths ([55e4bef](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/55e4befb349b50e69f153ccdfb496bc14380b7f1))
* sync uv.lock version with pyproject.toml 3.23.1 ([ab8c1f1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ab8c1f11dcd7c7857103ed0e1f2c329a8cff552c))
* **sync:** fallback when db has no savepoint support ([4d3e3b5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/4d3e3b587a64ebe2c84584187c3d2510a88ff24d))
* **tariffs:** support external squad uuid ([52424b6](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/52424b621a813472332a68ef93e45045d5df41cf))
* **tickets:** downgrade unreachable chat reply errors ([e7424c3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e7424c3a91faf97901e6893d1c687c20da297c5e))
* translate required channels handler to Russian, add localization keys ([bf83509](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bf835094cab92c4dc5a2933df3d915a8ff338462))
* translate required channels handler to Russian, add localization keys ([1bc9074](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1bc9074c1bcdaba7215065c77aac9dd51db4d7c8))
* **trial:** enforce global device limit over tariff ([d543122](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d54312242fde5a5dac99d9201cff5022505ace9d))
* **types:** resolve mypy issues in external and utils modules ([bf9cbcc](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bf9cbcc0276decb9d808eb351344746ecb735126))
* **ultima:** auto-activate tariff after top-up ([153d069](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/153d0693a50dc05548f9b4c4f6d4f736e9637b02))
* **ultima:** bypass onboarding flow on start for new users ([8526817](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8526817716d010fefe95a3c44cab02244492ce13))
* **ultima:** correct trial-to-paid auto-purchase remnawave sync ([b3a768b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b3a768bed1ac6e221100a3c0cf77534b3ef18345))
* **ultima:** enforce miniapp-only buttons after promo offer claim ([0796cc9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0796cc922196176dcfa9fd7ca28614d19cf621c2))
* **ultima:** enforce notification keyboard filtering across auto-renew and payments ([0279a9a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0279a9aacfc36defbf2120152deece81a12b92c1))
* **ultima:** remove bot-menu buttons from user notifications ([f199804](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f199804bf807c0f5b04e79a840ee41b1c8ec817a))
* update promo group via M2M table so admin changes persist ([7d3c809](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7d3c809ab3c1a6d02802acebe53483c66131ce3d))
* **updates:** enforce PEDZEO repos in admin releases endpoint ([08ef64a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/08ef64ac920cc4dbe06cfb7c3c641239aec371c4))
* **updates:** pin telegram update checker to fork repository ([23d6814](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/23d681429a1b5783df752a373fd13ef16f239b7f))
* **updates:** use PEDZEO cabinet repository for release links ([94deff3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/94deff3551f70a45dfc315d9cef13e3fbfe1ef3a))
* uploaded backup restore button not triggering handler ([ebe5083](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ebe508302b906f8b56cb230b934fb8566990c684))
* use .is_(True) and add or 0 guards per code review ([2b3587d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2b3587d7ab65e2c5d2f1780f2b8fe499c2ba7ba4))
* use aiogram 3.x bot.download() instead of document.download() ([16b10fd](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/16b10fd4fc412a797476b713c1c8692bd02b21fc))
* use aiogram 3.x bot.download() instead of document.download() ([205c8d9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/205c8d987d93151a17aa0793cb51bd99917aea97))
* use direct is_trial access, add missing error codes to promo APIs ([dc49252](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dc49252e5a3b556eeeea473034d4ceffa05bec07))
* use float instead of int | float (PYI041) ([978a8e0](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/978a8e0ead8737c39fe27a4be2195228bf3a7cd0))
* use SAVEPOINT instead of full rollback in sync user creation ([48e4417](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/48e441759e2d33a94e30aae62c6446f3ca9436e5))
* use sql table checks for db bootstrap ([086b709](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/086b70915a4520f931eb2dcc1eb07439479b34aa))
* user deletion FK error + connected_squads None TypeError ([e1886c5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e1886c57404ea902ea2e333320327add41750e39))
* wire cabinet rbac routes ([3997dbb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3997dbb710b99683d9f5ad39db27790b50e16607))
* гарантировать положительный доход от подписок и исправить общий доход ([0563786](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0563786797d1269c305af873b15e431defe73b48))
* добавить create_transaction для 6 потоков оплаты с баланса ([ec56f96](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ec56f96e2c218573897608ee17e6d2c196de5991))
* добавить create_transaction и admin-уведомления для автопродлений ([10dd6ac](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/10dd6ac7a6bfeaaf84e8394b4fde0b53e0ba16b0))
* добавить пробелы в формат тарифов (1000 ГБ / 2 📱) ([390b943](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/390b943a2549c96f2b8ea5ac9b4b590be94831cf))
* дубликаты системных ролей при переименовании и сброс permissions ([01ce477](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/01ce4771bd9b3bba44be8ed5cbcc5f25654275dd))
* изолировать stored_amount от downstream consumers в create_transaction ([af7ee03](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/af7ee032689a3eb8cac95e2b06bb51749a6588b8))
* исправления системы реферальных конкурсов ([be7d626](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/be7d626eea0a192524f83a29389ffb67a1b4e704))
* кнопка «Назад» в тарифах ведёт в админ панель, а не в настройки ([0bd792d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/0bd792defdc345a5b495c742caf60335e472c856))
* передать явный диапазон дат для all_time_stats в дашборде ([a7ee6ca](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a7ee6cade637b2ea17d80084b73be5daa44841d8))
* показывать кнопку покупки тарифа вместо ошибки для триальных подписок ([7dc9f46](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7dc9f46ec6f897e8c873d71d7e8059a53aede14f))
* промокоды — конвертация триалов, race condition, savepoints ([e9ce548](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e9ce548c8495624f5fcb2d578546ca599526526f))
* реактивация DISABLED подписок при покупке трафика для LIMITED пользователей ([49e5a14](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/49e5a141a474ada8e6aabc774b438b196b9b0f68))
* реактивация DISABLED подписок при покупке устройств и в REST API ([7c0ce3f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7c0ce3f028415a5ff871d6f4aa94ffc351e68119))
* синхронизация версии pyproject.toml с main и обновление uv в Dockerfile ([7df5940](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7df59401c55363b74eb7469c7fc2e9a758738c1d))
* убрать WITHDRAWAL из автонегации, добавить abs() в агрегации, исправить all_time_stats ([53714ae](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/53714ae5d757d07766defb960d417a005465c069))
* убрать избыточный минус в amount_kopeks для create_transaction ([f81439a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f81439a3849ec63315a73b520c490bef53162775))
* устранение race condition при покупке устройств через re-lock после коммита ([ede87ee](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ede87eeb126d6dd89c5ba0463d245bfd310bcdf2))
* устранение race conditions и атомарность платёжной системы ([8351ab1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8351ab1e21a42a3bcae3a3e928eae4b239fb2bfc))
* устранение каскадного PendingRollbackError при восстановлении бэкапа ([6d7688c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6d7688c4f172955b0012057ecd8e54289dd46f50))


### Refactoring

* align settings model_config with pydantic v2 API ([9144a4a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9144a4a01477b5b855d95377f83950565103b5cd))
* complete uv-only dependency workflow ([b1ad9ff](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b1ad9ff314489651acabf24924b06e60c030b9bd))
* isolate runtime shutdown args builder ([edaec72](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/edaec727650910f47f1a67879f0931f0acd41513))
* isolate web shutdown args builder ([5821db5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5821db5d0c9cafceeb98a3347c20fdeaa0f054d1))
* make finalize() accept both old and new pricing types ([bd018e1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/bd018e164d39727b6d8291b8db26fc7165e47088))
* migrate admin user price calculation to PricingEngine ([eb76cb2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/eb76cb2a6c960fffe1609d3e3de42f33375cc03c))
* migrate bot renewal display to PricingEngine ([486f8b8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/486f8b8931be83a1f77aa605ad1db6113a1a8716))
* migrate bot renewal execute to PricingEngine ([7399f0e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7399f0efd3a9ca1ebc05ecbde73dd6309c186437))
* migrate cabinet renewal display + execute to PricingEngine ([ae91ecb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ae91ecba63a1b6457093be24050dd3eded55794e))
* migrate cart auto-purchase to PricingEngine (fresh calc) ([5de288d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5de288df452dfc7d932f1b5417f9e36e6c239c06))
* migrate menu.py renewal pricing to PricingEngine ([ce149dc](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ce149dc36626c59cc4001f8f2927c332640c50ca))
* migrate miniapp renewal display + execute to PricingEngine ([3c6dff0](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3c6dff029660e487f1931f269ce5a469b3901a2f))
* **miniapp:** centralize subscription update finalize flow ([cd33859](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/cd33859b91b67ad91cc3f712b3733a63c8961f7e))
* **miniapp:** centralize tariff switch pricing and messages ([428ea1d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/428ea1decf49e660a4d5af7aec0a76345b17aa0f))
* **miniapp:** extract auth helper module ([2d60f75](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2d60f75233129c50b3c3d9b42d2cdf85391fe42d))
* **miniapp:** extract autopay helper functions ([e313cc5](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e313cc5b169aa426fe82f5d44cc272fc7009e139))
* **miniapp:** extract cryptobot helper module ([6ab7124](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6ab71246a12c7e209a2af58510a19212156d867d))
* **miniapp:** extract daily subscription toggle helpers ([69220cc](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/69220ccf31316870a0848048d09cd71ffc9afd08))
* **miniapp:** extract datetime format helper ([b5f2d74](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b5f2d74c4d956d4ccacccb4019e55ab1da087d8b))
* **miniapp:** extract misc helper module ([6040065](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6040065bd1c87acbb8e131fcee868fbe068045a1))
* **miniapp:** extract payment amount helper module ([7944f9e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7944f9e53a9fafc91fe4b9c99441de419b140948))
* **miniapp:** extract payment create input and cryptobot handler ([adcfe01](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/adcfe010e76ce1c72f6fc62c00d85946f9559150))
* **miniapp:** extract payment lookup helper module ([8bd6796](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8bd679662c338a7f085cc19d3754bd00a4194ca2))
* **miniapp:** extract payment method status helpers ([87127de](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/87127ded2a94e0b6851c65484303eb96addb83a9))
* **miniapp:** extract payment request helpers ([df7d6a8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/df7d6a898631ee235fb0803077972bb228ac907f))
* **miniapp:** extract payment status classification helper ([16a77ee](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/16a77ee1f500b060f0cc71eb6c8098f2ebe31534))
* **miniapp:** extract pending payment status builder ([291cdff](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/291cdff6fec3ccc389d414a632a95b8d8b05f644))
* **miniapp:** extract promo discount helper module ([1915ccf](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1915ccf235af7e3e317afb382a78c21d6bb36bff))
* **miniapp:** extract promo offer helper module ([d548fa4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d548fa47b23d458be95aa6dc992c1f514401b9a0))
* **miniapp:** extract purchase selection helper ([a6b7b59](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a6b7b59a58edf319a219a69c4767cca60865f181))
* **miniapp:** extract renewal message helper module ([c81486c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c81486c799cb38e940d0f81fb2736b69b384e598))
* **miniapp:** extract renewal submit parsing and payment helpers ([281a90c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/281a90c1e7aefb74c5c981e32b38ba63263844d2))
* **miniapp:** extract shared formatting helper module ([aa85093](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/aa85093ecb9a6ddf1ce388f843023da9cc2391fa))
* **miniapp:** extract subscription devices update logic ([9f7eaec](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9f7eaec6ae02225f07f973e4191b157195ebc7b9))
* **miniapp:** extract subscription helper module ([3345b4a](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3345b4a0b3389f6ba72f7a51a47f8ef5750b4a1d))
* **miniapp:** extract subscription servers update planning and apply flow ([5e1e7d1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5e1e7d19c82f7ccc78d7c02b029112f9c89c8fc5))
* **miniapp:** extract subscription traffic update logic ([dab20a2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dab20a260dbde994dcb5473b1977430844e643d9))
* **miniapp:** extract tariff helper module ([e598e9e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e598e9ea1d0d8930dc3addcdd60a66ceedb3c3a2))
* **miniapp:** extract tariff purchase context and balance checks ([a3d1464](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a3d14644178066a3c06dae8f56f6839ebf504090))
* **miniapp:** extract tariff switch pricing helpers ([29f9fb4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/29f9fb4a2cb3cbe4ffe88dd81a90c1361221253d))
* **miniapp:** extract tariff switch validation context ([9249b70](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9249b70482fb8f60c648fe7d77078a98a3a38521))
* **miniapp:** extract unknown payment status builder ([d41a107](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d41a107408f26113eac193a1cf4e767d4fe22586))
* **miniapp:** extract yookassa payment create handlers ([a3365bd](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/a3365bd379635d6f8e2326b9f190fc60dfd37a36))
* **miniapp:** group payment helpers into payment package ([b7e057c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b7e057c6df454dc23ce3db2a0cec4bbe0a503305))
* **miniapp:** group promo helpers into promo package ([44670f9](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/44670f9b55d866e017b60adc3369c38711db0d58))
* **miniapp:** group subscription and tariff helpers into packages ([d445e27](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d445e2743f2c4ba607f7e7eed0c4072129ee3fd0))
* **miniapp:** move base payment status resolvers to module ([551f443](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/551f443d1ea07a479b77cdd7bc842637598c5295))
* **miniapp:** move daily resume remnawave sync to helper ([c2ed68d](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c2ed68de4c022ce7c58c5c4c15685bf146169cdb))
* **miniapp:** move direct payment status resolvers to module ([2ea9ab8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2ea9ab8721143fc236d3e00cdc04776599fbec56))
* **miniapp:** move gateway payment status resolvers to module ([2179dea](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2179deabf3e538a43d634468db1625b2f5193b03))
* **miniapp:** move init-data user resolver to auth helper ([efe20df](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/efe20dfb1e498d2d3fe85f97b48f5d20b8d58334))
* **miniapp:** move payment status dispatcher to module ([b226242](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/b226242157c61d1efab2e86810b5c2f3447e704f))
* **miniapp:** move promo offer model builders to module ([ca7e761](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/ca7e76183bf789b84dbea645b3765d7d17436ced))
* **miniapp:** move referral info builder to module ([c89028f](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c89028f345889e8b225f177d7ffddb7adffbd8c8))
* **miniapp:** move renewal cryptobot flow to helper ([1063c88](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1063c885ea3bcd66c95032fafcf6409293675ae7))
* **miniapp:** move renewal execution paths to helpers ([c7acbeb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c7acbeb77c1a934f3e34ba773d179665c55306be))
* **miniapp:** move renewal options builder to helper ([5ffeefa](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/5ffeefa1dfb613515d24bdc919d43d2ffb0508a3))
* **miniapp:** move subscription runtime helpers to module ([eddabe4](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/eddabe47d0686bfe2a31441e0be3d605d2c35b07))
* **miniapp:** move subscription settings builders to helper ([feb59d1](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/feb59d1d434fe3822b94370b796d0fdba680e225))
* **miniapp:** move tariff api model builder to helper ([503b590](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/503b59032eabc19f4b85d93fcf5c4b20858bd455))
* **miniapp:** move tariff switch charge transaction flow to helper ([c39e26e](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c39e26e20f512277959ce3c833a7f7d794885a7c))
* **miniapp:** move tariff switch subscription mutation to helper ([1f06806](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1f06806f77c7b6013583e619414fd2e3e03c1fde))
* **miniapp:** move tariffs endpoint payload assembly to helper ([76d2d55](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/76d2d551482b9f29a311fd4aca9e3ad919871462))
* **miniapp:** move traffic topup execution flow to helper ([1da3d32](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1da3d321881d5b55c972872a50140be2d08a5079))
* **miniapp:** move traffic topup validation and pricing to helper ([dc7b863](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/dc7b8634328893f3ec9051e103e55585a71c68cc))
* **miniapp:** move trial and current tariff state helpers ([6140651](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6140651f100ed47cf7e16c63a745a77a8122e70d))
* **miniapp:** organize helpers into miniapp_helpers package ([3d22800](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/3d22800e72e580f449de3011334a2401226c7803))
* **miniapp:** reuse pending status helper for pal24 ([1cb17b2](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/1cb17b22b3e7b925a4a0c40713d5e5eda0e54aa6))
* **miniapp:** reuse pending status helper for platega and wata ([2c655cb](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/2c655cb8d1d060d23a59618833c41eb3d5a5d17d))
* **miniapp:** reuse shared tariff squad resolver ([f813e34](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/f813e345bb267e4572acb418ea8b2eca070f7f71))
* **miniapp:** unify tariffs-mode guard via helper ([8378064](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8378064fa45767029aa9cd6f92d41c5f0561e0a7))
* remove estimated price from balance, simplify server sync, fix HTML injection ([53c80e7](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/53c80e7bcac3b9eb2e09a49098c4a0b92efc9ceb))
* remove legacy app-config.json system ([295d2e8](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/295d2e877e43f48e9319ba0b01be959904637000))
* **subscription:** extract app-config deep-link helpers ([c0789b3](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/c0789b374baaea2c89b7c5f22e265ead6cfe5782))
* **subscription:** extract shared route helpers module ([d78a9db](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/d78a9db134f3e381a8d5f434cca2c5ae72b361d1))
* unify first-purchase discount algorithm with PricingEngine ([7a7a51c](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/7a7a51c1ce5c377897503dbc45bb821665f87c1d))


### Documentation

* clarify fork differences for users ([8a46a9b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/8a46a9bbd1a0d8ca63740ede5525fcba9a5ec1da))
* remove fork audience section ([e813803](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/e8138036bf331e649ad8ad2bd53dbcc2696c41ec))
* update chat invite link ([6b5ff7b](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/6b5ff7be919a47b6c3c50aabf0483be20c84a721))
* update test bot and contact handles ([9f69726](https://github.com/PEDZEO/remnawave-ultimteam-telegram-bot/commit/9f6972635162172cf4de3b1cff2dcf6492131900))

## [3.25.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.25.0...v3.25.1) (2026-05-27)


### Bug Fixes

* **news:** return relative media urls ([2f535a9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2f535a92e058857655bc676c6e08b4e31b6f1b34))
* persist ticket media replies ([b28a415](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b28a41552b4e66807220ac6b3747f26fadd9c506))
* **tickets:** downgrade unreachable chat reply errors ([e7424c3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e7424c3a91faf97901e6893d1c687c20da297c5e))

## [3.25.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.24.2...v3.25.0) (2026-03-31)


### New Features

* add managed news categories and tags with DB-backed CRUD ([bd2e085](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bd2e08590a47b211cbd4313ae81955522d07ef08))
* add media upload/delete API for news articles ([0cfdc38](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0cfdc3882bbb43a2081d5146fa79fb120d90d902))
* add news articles module with admin CRUD and public API ([c1c0423](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c1c04234eca837b1bc9a81f5f68c1148e974c646))
* add ultima provider account linking mode ([9fe7998](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9fe7998d4aa43febfadc366512476c9d1c35f937))
* add ultima theme presets ([754af78](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/754af78dfcb34088da1607f230697cc915b5fb1a))
* **api:** expose email field in UserResponse ([6fcc20f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6fcc20f4358c754f50497fc69356285accc7c140))
* **branding:** add ultima theme config api ([c316189](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c3161895b0b027312bf373e9c6a40d8c6202deb1))
* **branding:** support ultima framesEnabled in theme config ([f96b61d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f96b61dc70ff7e5bd51695c198369d3531d49b87))
* **branding:** support Ultima home logo toggle in theme config ([61b21e3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/61b21e30a03ea017593904ac946071d97e7e1d13))
* enforce single featured news article — unfeature others on toggle/create/update ([f222b4b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f222b4bf4d041d9046150a23e08674c9e2cfa86c))
* expose MULTI_TARIFF_ENABLED and MAX_ACTIVE_SUBSCRIPTIONS in admin settings ([ccb311f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ccb311f262cd4fcacab99a4f464173e18ff0c94b))
* **tickets:** add user endpoint to close own ticket ([b68d0cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b68d0cb375301502bf039b6877ac5251146b2e6d))
* **ultima:** add configurable notification buttons for bot alerts ([c0e3875](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c0e38756f07eac034929eea8ef0e2b9d46bfe25c))


### Bug Fixes

* add blocked user support button in bot ([e99f6e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e99f6e581bfad161d5096e9fa42905a74bd82250))
* add classic waves animation preset ([a8378dd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a8378dd3b5c7811651da4fc948f914cb1f54b50f))
* avoid invalid ultima notification webapp buttons without miniapp url ([11299da](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11299da0ea6a3797979d0b4692da31f889464cf9))
* avoid locale writability warning when no template sync is needed ([53323ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/53323aeb0aeca4919ddc96e12ffaa3600d9cb9e2))
* **bot:** harden user and notification flows ([d480af6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d480af682224b834b04e51cd551106726d239654))
* **ci:** sync uv lock for 3.24.2 and harden release lock workflow ([2c618a7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2c618a7687048b4733c34f2dc64243c0f373b739))
* **db:** repair missing tariff external squad column ([e230a3f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e230a3f1a3cca2d96a8951860ee77fedd4feb0ab))
* disable post-topup cart flow to avoid duplicate notifications ([dc6d360](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc6d36010fb3666a94baf3696902fdc2fe656c0a))
* disable topup cart notifications only in ultima mode ([bcc2adc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bcc2adc6cdd037e5d3f1ba4fce56d96102e1dbeb))
* ensure admin gift notifications for purchase and activation ([f59d685](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f59d68555f72aeb43810267e82ae694a277cb96f))
* **gift:** prevent double activation and enforce delivered status ([3890d12](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3890d12ef85c241bad75a3f8074bde2b759ba60a))
* **gift:** reject reused gift promo and stack gift days ([e51a070](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e51a07030212c180179273361a2b6a4caa1243ce))
* **gift:** unify already-used promo error code ([dc1fa2e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc1fa2eedb1d53c7e18aa1cb80ce24098ae9bfea))
* harden admin subscription notifications delivery ([5a96a2e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a96a2e15f051c3cdbd1e8f32c82a114405da1f0))
* linearize alembic gift migration chain ([fc1b210](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fc1b2101d00039860f8a2607740e7f5b3eb4d70b))
* **migrations:** bootstrap fresh databases at head ([11c87e1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11c87e1f7ac827a00292abe9f06329edbe786eca))
* **migrations:** normalize overlapping alembic revisions ([d21729a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d21729aae2d063d835dca7b9f56e8663226d4dcc))
* news module security hardening, perf optimizations, bug fixes ([7c3d006](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7c3d006090be8d13e65f0dadfe4811b31b65f754))
* **news:** adapt permissions and migrations for fork ([6c6bed3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c6bed3a2143d2c69f2b7be743e04611e220cc3d))
* **news:** serialize list queries on shared db session ([ec40c09](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec40c09c7d3b84ff8e5d74bf6387b026838e4168))
* prevent missed gift admin notifications in cabinet flows ([d9514f6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d9514f6abdfb21651b9c4122de9404dd8dbe8344))
* **promocode:** return stable gift reuse error ([614e1b0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/614e1b0bcd08d9e6e5d10d151f23e016310adc57))
* register categories/tags/media routers before news to avoid route conflict ([3a5e385](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3a5e3857bc5c6893905f25e17b4e1136e706d097))
* reject occupied direct identity links ([ffa2933](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ffa29331962531b9ecb7c5088122406dd104c7e5))
* remap squashed alembic revisions ([171abe5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/171abe5365433f4cdc6e8dd30c266169fafdc262))
* remove duplicate gift admin alerts from cabinet routes ([21fae07](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21fae0757870fdcf146bf4cc3553577d2b510e31))
* restore settings import in gift config route ([59ceb71](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/59ceb711e3fde0764148d82c8ef76cc5e72f4dbe))
* send gift admin alerts via generic notification channel ([186ead3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/186ead3f0ccf9c71698157e25c8806bb4caac988))
* show tariffs for legacy users without promo group ([aa1923f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa1923f391e117c7eb65367b565bb00a9d866cf3))
* silence optional locale sync warning on read-only mounts ([27831ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27831efcebcfc0bcda1b4dc5d2aecad72c323805))
* stabilize backend ci imports ([7a4fb1f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7a4fb1f264767ceab206d66c77a449b3289e3798))
* **subscription:** refresh stale remnawave links ([80c834a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/80c834a10cfff6fc58fee875f62b1ad6ece2ec14))
* support non-committing notification cleanup in subscription flow ([55a131c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/55a131c8c0dfa4e9faf0a306c5ae8c8910bbe026))
* **tariffs:** support external squad uuid ([52424b6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/52424b621a813472332a68ef93e45045d5df41cf))
* **ultima:** auto-activate tariff after top-up ([153d069](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/153d0693a50dc05548f9b4c4f6d4f736e9637b02))
* **ultima:** correct trial-to-paid auto-purchase remnawave sync ([b3a768b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b3a768bed1ac6e221100a3c0cf77534b3ef18345))
* **ultima:** enforce miniapp-only buttons after promo offer claim ([0796cc9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0796cc922196176dcfa9fd7ca28614d19cf621c2))
* **ultima:** enforce notification keyboard filtering across auto-renew and payments ([0279a9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0279a9aacfc36defbf2120152deece81a12b92c1))
* use sql table checks for db bootstrap ([086b709](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/086b70915a4520f931eb2dcc1eb07439479b34aa))

## [3.24.2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.24.1...v3.24.2) (2026-03-14)


### Bug Fixes

* **build:** refresh uv lock for release 3.24.1 ([60a8b64](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/60a8b64592526429488888c028a1012ce304290d))

## [3.24.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.24.0...v3.24.1) (2026-03-14)


### Bug Fixes

* **build:** refresh uv lock for release 3.24.0 ([6f0cd89](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6f0cd89101df5d2e514b22d7808a921a6e8f9587))

## [3.24.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.23.0...v3.24.0) (2026-03-14)


### New Features

* add CLASSIC_PERIOD_PRICES to config ([ad79130](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad7913078b823f5b2dcfc0e865f7fcfb0dbe7363))
* add gifts section to admin user detail API ([e0561f0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e0561f08f0378d192b6adf294df37089f98ffb6f))
* add LIMITED subscription status and preserve extra devices on tariff switch ([06dd0f8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/06dd0f8a49fa281f5ee2ab0fc20ae04331c85cca))
* add promo group and promo offer discounts to gift subscriptions ([4ab64fb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4ab64fb241902cfbc44c766d03b5fbc585208f08))
* add RenewalPricing dataclass and PricingEngine discount methods ([0a24db7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0a24db7bb94258db127b51ee5a4d115685b1f7d8))
* add show_in_gift toggle for tariffs in admin panel ([74258b2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/74258b245193acf64a2954dac730848a218186eb))
* add sync-squads endpoint for bulk updating subscription squads in Remnawave ([dabd1f1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dabd1f1cc9b864160954087b382ee1f3228ef2f7))
* auto-sync squads to Remnawave when admin updates tariff ([e1ee6bf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1ee6bf911d7adbc6d1de68f2fbf69f5adbd275e))
* **cabinet:** add default subscription payment method flag and tariff max devices ([f7976c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f7976c9479c020946010395c66d9803930ded8aa))
* **cabinet:** add ultima mode branding endpoints ([42e1b3d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/42e1b3dce553a29bc71c751b85aaed43d3e1fc8d))
* **cabinet:** support device_limit in tariff purchase pricing and activation ([38932d9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/38932d9cb637426490dd24ad20b5168eb0e021ca))
* **gift:** allow extending gifts with selected period ([b8b8186](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b8b81865f1837220443c21a25dffe06d04dc9c9a))
* **gift:** sync upstream gift subscription backend flows ([83c4d10](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/83c4d1036b6150f1c73941c942574f7acf51448e))
* **promocode:** return gift sender in activation response ([1c59e31](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1c59e318b5342baec5a0a4b90f495680473bddb5))
* referral links now point to web cabinet instead of bot ([b4cd176](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b4cd176b04667e462fe0dc4ca31e67573b82566e))
* return detailed insufficient balance for gift extension ([ae14fa3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ae14fa388c3fb84cdf5114a9674a8daea95d3376))
* support extending existing gift tokens ([b6d15ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6d15eecba559fc9b2283813d7a8a346d883d34a))
* **ultima:** add standalone agreement endpoints for user and admin ([cec96e6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cec96e6d7283b3c0f1e2b12bafe4e2ac673b7cbd))
* **ultima:** separate start flow with configurable app message ([7da6101](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7da6101012a7f4f6db47e5e3f3fdb5977f5a838d))
* **ultima:** support gift promo flow with partial top-up ([f4ffc98](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f4ffc98f50e3a3c18ebaa417bcb3c5951f824328))


### Bug Fixes

* add missing settings import in admin_users tariff switch ([b849ad1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b849ad1594c71476bf7c1d3e738b44198230757d))
* add nested selectinload and referrer eager loading to prevent MissingGreenlet ([9d80077](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d8007788a7d82fe1f8c182a5b2c3638c05ed12a))
* add per-category discounts and months multiplier to classic mode ([254a412](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/254a412978082e16a5198b786cf5dbeacf8cc836))
* add period_days whitelist validation and type annotations ([3c35022](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3c35022cd5104c2eb5e459a2baeac81962c16edf))
* add post_update=True to User.referrals self-referential relationship ([5d52d24](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5d52d24dbe52155e27c2b0325b45d2edbff31637))
* add selectinload to user lock queries to prevent MissingGreenlet ([529c3f1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/529c3f1ccd21456d895a3320b82c77f77ae0e3c8))
* add Telegram Stars payment support for gift subscriptions ([dfdec12](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dfdec12cc2a52b47863dae72c34a3367f38332a3))
* align guest purchase service with fork architecture ([7241663](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7241663f5419843bb865d7082d074147b4ee1c88))
* append cache buster to generated miniapp urls ([c869559](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c8695597575f640535d21aed95e575b404e68bfd))
* atomicity refactor, review fixes, and DELETED recovery logging ([dc86d18](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc86d188fb84a81754de5eb61b4707c0ea7cfbe0))
* **auth:** make refresh JWT unique with jti ([38f9f6c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/38f9f6c190bab01d9f4e20f17f2e5775884347ca))
* change None assignment to [] + add "or []" guards at all 5 call sites. ([e1886c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1886c57404ea902ea2e333320327add41750e39))
* correct skipped_count in sync-squads circuit breaker and simplify ternary ([475bf6f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/475bf6f490e630e6fa6172c461b414115872551a))
* define UUID pattern in tariff schemas for external squad ([45ee3f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/45ee3f2b23008d8ae92eba7d4507f854b27bbdf8))
* downgrade known-harmless RemnaWave 400s to warning level ([2a2ddf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2a2ddf57fbb6079a5f5e7c4be30c72d4c1bc67c5))
* fallback balance lock for mocked sessions ([06f8fa2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/06f8fa2e293d4600bcb6a56399245d484ab11639))
* **gift:** enable gift flow automatically in ultima mode ([4b56687](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4b56687e4de482e81bc5d6eaad8d0e058f26cddc))
* **gift:** fallback to active tariffs when show_in_gift is not configured ([2baa1c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2baa1c97d9b1929d44c00e603c46943d5f336d7d))
* **gift:** respect gift toggle and restore settings import ([ed8352f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ed8352f3f21ce6aec687e2b7dd3c67121fa9fecc))
* guard rollback on commit flag, add flush to promo_offer_log ([59d99bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/59d99bdd42a99862ababeeb5e3397f44c03a9c4e))
* handle legacy telegram_id in YooKassa webhook recovery metadata ([5c3204e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5c3204e84727aad158e3170154ca21f00cc4e82e))
* harden remnawave API error handling and YooKassa user cross-validation ([2156784](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21567846a5581000ab80c3d9f4bf3e16376c08ad))
* harden YooKassa webhook recovery user lookup ([e7342b5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e7342b5495d47f7e7f98bdadaadebedf31d7db15))
* invalid ISO date format in node usage stats API call ([93aedaf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/93aedaf277f745f15baf0bb4b1b14219a576a7a4))
* keep payment lock flow compatible with mocked sessions ([e1ad616](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1ad6162245e0b38f82f148a716e94daec5b8cfe))
* **migrations:** add 0037 compatibility placeholder revision ([c13e79d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c13e79df5f01ab21ad5e19cff53c62ab6401240a))
* **migrations:** make 0019 gift migration idempotent ([8361467](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8361467ae2f6665507c3ad5b9dbbf24e38a1118f))
* **migrations:** make unique constraints idempotent for 0015 and 0017 ([fffc122](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fffc1223e82986969bd9ba120377c4ff94f10e2e))
* payment providers — lock_user_for_update + commit=False atomicity ([709e0a6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/709e0a6c6e2b21eaa51468e8bd259c44e29b01d7))
* platega webhook ID fallback for SBP and card payments ([8c53fb5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8c53fb5f9d1e00fc6b3d0a7044f8aefe937319a0))
* preserve purchased devices when admin changes user tariff ([6bef3f3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6bef3f39bb224ef76dd58b3280d83ebbc227eb11))
* prevent account takeover via auto_login_token, ensure promo group on all purchase paths ([ef6a129](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ef6a12911d2d3a6e54a7fc199421cad2347fd81c))
* prevent balance loss on auto-purchase for DISABLED subscriptions and fix WATA expiration ([8d70fa3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8d70fa383d9d4dd4aead10b6ab44239069a7ae78))
* reactivate subscription after traffic top-up when status is EXPIRED ([4ab9f4b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4ab9f4b15e373882ca00e9e482695dc7178c7d9b))
* record transactions for free tariff switches and admin tariff changes ([ca028b8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ca028b831d1050e0b80ae9d669b5c2da3c247781))
* remove unused settings import in admin users route ([841d528](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/841d528e49023b4eb93d54881fdcb4e7cac14aea))
* reset subscription for paid users, trial-to-paid tariff conversion, gift purchase MissingGreenlet ([abf2882](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/abf288232d383be202b0d0f8c96cbabdaabcebda))
* resolve MissingGreenlet in switch_tariff endpoint ([f610df3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f610df3a997c411669b63f1d4d118070688d6ec0))
* resolve post-sync renewal response and typing issues ([931027e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/931027e0b8ad70395b1af579b92a41c38f4280dc))
* resolve post-sync typing and runtime issues in auto-purchase ([3fbc8fe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3fbc8fec80f434e17b9547a22b81d58b14a605f2))
* restore miniapp payment status classification and stabilize auto-purchase tests ([7aa464f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7aa464f225ecdff614a197dc4d4f6f7feccd5cd6))
* **settings:** allow admin trial overrides over env ([e4cc0ed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e4cc0ed582d550b323da3532c296e434d4902159))
* silence PARTICIPANT_ID_INVALID error in channel subscription check ([4ef8599](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4ef8599a9c370e1e82c5082f733b4ea7e5824b0c))
* **trial:** enforce global device limit over tariff ([d543122](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d54312242fde5a5dac99d9201cff5022505ace9d))
* **ultima:** bypass onboarding flow on start for new users ([8526817](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8526817716d010fefe95a3c44cab02244492ce13))
* **ultima:** remove bot-menu buttons from user notifications ([f199804](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f199804bf807c0f5b04e79a840ee41b1c8ec817a))
* update promo group via M2M table so admin changes persist ([7d3c809](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7d3c809ab3c1a6d02802acebe53483c66131ce3d))
* user deletion FK error + connected_squads None TypeError ([e1886c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1886c57404ea902ea2e333320327add41750e39))


### Refactoring

* make finalize() accept both old and new pricing types ([bd018e1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bd018e164d39727b6d8291b8db26fc7165e47088))
* migrate admin user price calculation to PricingEngine ([eb76cb2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eb76cb2a6c960fffe1609d3e3de42f33375cc03c))
* migrate bot renewal display to PricingEngine ([486f8b8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/486f8b8931be83a1f77aa605ad1db6113a1a8716))
* migrate bot renewal execute to PricingEngine ([7399f0e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7399f0efd3a9ca1ebc05ecbde73dd6309c186437))
* migrate cabinet renewal display + execute to PricingEngine ([ae91ecb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ae91ecba63a1b6457093be24050dd3eded55794e))
* migrate cart auto-purchase to PricingEngine (fresh calc) ([5de288d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5de288df452dfc7d932f1b5417f9e36e6c239c06))
* migrate menu.py renewal pricing to PricingEngine ([ce149dc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ce149dc36626c59cc4001f8f2927c332640c50ca))
* migrate miniapp renewal display + execute to PricingEngine ([3c6dff0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3c6dff029660e487f1931f269ce5a469b3901a2f))
* remove estimated price from balance, simplify server sync, fix HTML injection ([53c80e7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/53c80e7bcac3b9eb2e09a49098c4a0b92efc9ceb))
* unify first-purchase discount algorithm with PricingEngine ([7a7a51c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7a7a51c1ce5c377897503dbc45bb821665f87c1d))


### Documentation

* update chat invite link ([6b5ff7b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6b5ff7be919a47b6c3c50aabf0483be20c84a721))

## [3.23.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.22.4...v3.23.0) (2026-03-06)


### New Features

* add admin sales statistics API with 6 analytics endpoints ([69c5323](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/69c5323e1be0b001c4dd286d64f66084de382e2c))
* add daily deposits by payment method breakdown ([c338977](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c338977ba52469108200166774ae64e92de8d15a))
* add daily device purchases chart to addons stats ([4388d3b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4388d3b297a87bae2fe647ce9f8d65159acc6e70))
* add dedicated sales_stats RBAC permission section ([e642475](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e642475bb8c697961f8d160671feb68c4651219c))
* add desired commission percent to partner application ([6016128](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6016128630221c69ec77a41508985b4f12c0a7a6))
* add RESET_TRAFFIC_ON_TARIFF_SWITCH admin setting ([2d1bc4e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2d1bc4e15451f619536b82347f8ad4aa30970fbc))
* enhance sales stats with device purchases, per-tariff daily breakdown, and registration tracking ([732409c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/732409cc76719b82924f49fde849693d70d63d43))
* replace pip with uv in Dockerfile ([9031ab2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9031ab253e5292988effa96d2a6f1345dd11f0da))


### Bug Fixes

* abs() for transaction amounts in admin notifications and subscription events ([630a018](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/630a01845ec2f8bafddb6a6e0bf2fa3e59e28d53))
* adapt user FK ondelete migration for fork graph ([4df5b43](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4df5b435906b1153c8ec0b865d9e319fbe6d1279))
* add abs() to expenses query, display flip, contest stats, and recent payments ([e917b76](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e917b7667af52f5215f9ab58ad377d9de2f82ec9))
* add exc_info traceback to sync user error log ([427b53a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/427b53a47f9132df6901bf381150e4b3aa53ee7f))
* add local traffic_used_gb reset in all tariff switch handlers ([2727635](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27276350d964a7b443e58f80c9aebd6cac749845))
* add min_length to state field, use exc_info for referral warning ([35c6add](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/35c6add59b6a746720bb61eaeb4b180e7d170948))
* add missing mark_as_paid_subscription, fix operation order, remove dead code ([78caaf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/78caaf560b6de3bd28082d655962da296d2e86ee))
* add missing subscription columns migration ([7075e0e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7075e0e99ef59875143e01f8d8c6785041dcfbb1))
* add NoScriptError import fallback for redis test stubs ([39c6f8c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/39c6f8c4550de6cda0809b878be570ecb5673e04))
* address review findings from agent verification ([370208e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/370208ef4eab906a30047b04061e22db68a5af58))
* align migration tests with alembic heads target ([521f866](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/521f866e83d8371a2098a8a69bdf295bec3c3000))
* auto-update permissions for system roles on bootstrap ([d8f07b8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d8f07b8caf9d38efdfcc93da37088442aad18be9))
* centralize balance deduction and fix unchecked return values ([a527b8c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a527b8c4a5a45c8d193c8c93c1654c17a91f5581))
* centralize has_had_paid_subscription into subtract_user_balance ([7ff135c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7ff135c5dfd2f7da87bb69fe0e2302ba0a512f0c))
* complete FK migration — add 27 missing constraints, fix broadcast_history nullable ([1a5def2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1a5def29d8dbc9c59c92ceca38695a54cf67e975))
* consume promo offer on tariff balance flows ([c868149](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c86814951a3569332de61e8d50d6f33f6753df66))
* correct cart notification after balance top-up ([3c2746e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3c2746e5e87eb4f10d59e7dec0a5b7ac13b28c9f))
* correct referral withdrawal balance formula and commission transaction type ([d8a372d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d8a372dc6b5e4ad4ed5e19fce6ad76243e6cadaf))
* count sales from completed payment transactions instead of subscription created_at ([e8861bf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e8861bf1899f0a64accd8e6e4580926a2049a16b))
* device_limit fallback 1→0 для корректного отображения безлимита ([8581fec](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8581fec02ef937ff74f65b0be1aee61c12879173))
* eliminate double panel API call on tariff change, harden cart notification ([0937d62](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0937d62bf32cc7ceb25c2eb435fbb443b8b94f98))
* eliminate referral system inconsistencies ([0940897](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/09408976e7e49498e0a26b15f1acfee57df49849))
* email verification bypass, ban-notifications size limit, referral balance API ([aeda809](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aeda80932162d17edd9a4cd14109f1edceeb1d07))
* enforce user restrictions in cabinet API and fix poll history crash ([fb76cbb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fb76cbbde4f2c15f4e1becfb2a4a871d34f270a7))
* expose sales stats routes and align RBAC permission ([10780d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/10780d6ef09e9448cc5527409254f4a36dde0f7d))
* freekassa OP-SP-7 error and missing telegram notification ([dd306ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dd306ae6926e5532c9ea9fe067bf83d5c8bf7b47))
* generate missing crypto link on the fly and skip unresolved templates ([0bec636](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0bec63664646e1ed5f8f7ae0ab5fe95a9551cc6e))
* handle expired callback queries and harden middleware error handling ([df13ab1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/df13ab117526332ad77b5551e4b055491f15192d))
* handle expired ORM attributes in sync UUID mutation ([33bd6e4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/33bd6e42a03edad6cb184ca4a8d5a3a548631913))
* handle NULL used_promocodes for migrated users ([f017f91](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f017f9173e19e6a08a25180d9dea483111ecc523))
* harden FK migration lookup for missing constraints ([4240f01](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4240f01b399607dfff391d452c16ac27dba09de1))
* hide traffic topup button when tariff doesn't support it ([c92f7a5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c92f7a55e0cb814ec13e5a45f2a12759d8acfdb4))
* include desired_commission_percent in admin notification ([56a0cf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/56a0cf5cd7cc7c9ee9e6676a380797259af3763c))
* partner system — CRUD nullable fields, per-campaign stats, atomic unassign, diagnostic logging ([8494433](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/84944332b61f818542e6404090d37798438349ab))
* preserve auto-purchase admin notify and lazy websocket imports ([4bd1f0c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4bd1f0c73f23c3e7a0de8b1da8663e38d1de3ff1))
* prevent infinite reuse of first_purchase_only promo code discounts ([14bd19f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/14bd19f79568d695ccb1bfcd2a2e0c7e0d8fc256))
* prevent squad drop on admin subscription type change, require subscription for wheel spins ([5a7df48](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a7df483f95b91a30bece4b9e1d71ffa70ed9b05))
* prevent sync from overwriting subscription URLs with empty strings ([14082e4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/14082e46de4fdbd8e75a163b22b47b35e8d73684))
* reactivate disabled subscriptions before traffic sync ([692f30b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/692f30b772b31d5ac0ac4d98fef9998a71e91e65))
* redis cache uses sync client due to import shadowing ([7f0dd1a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7f0dd1a1b5a80bdcfd72b5612ff4c4ebf1bb79f4))
* reject promo codes for days when user has no subscription or trial ([7aec1e7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7aec1e7355223f2610d109b7edbff50ef0512d60))
* remove premature tariff_id assignment in _apply_extension_updates ([fa6e1b4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fa6e1b4a219e1244348b9518851d336044b2247a))
* renewals stats empty on all-time filter ([be29e1f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/be29e1f1349f31b124700e864e87a7d66ce77865))
* resolve alembic duplicate revision conflict for referral migration ([e33e942](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e33e942d154b59f5149165e07be48fc5929b604f))
* resolve GROUP BY mismatch for daily_by_tariff query ([de41378](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/de413784d89a70e9230968343ae11caf0a487079))
* restore panel user discovery on admin tariff change, localize cart reminder ([2ec1d30](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2ec1d309c2ae4dde0ca9631bf6fab2ff8b237cca))
* run alembic upgrade against all heads on startup ([fd789ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fd789aee1cce7c3f17e795cc8ac2035255600b13))
* separate base and purchased traffic in renewal pricing ([3211d98](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3211d98fdbfe75c0f6d7da63ac48d7565bcc57dd))
* stabilize upstream payment sync and webhook compatibility ([c25e772](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c25e77237ed19be7b092cf93c18302cee5c54a77))
* sync traffic reset across all tariff switch code paths ([55e4bef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/55e4befb349b50e69f153ccdfb496bc14380b7f1))
* sync uv.lock version with pyproject.toml 3.23.1 ([ab8c1f1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ab8c1f11dcd7c7857103ed0e1f2c329a8cff552c))
* **sync:** fallback when db has no savepoint support ([4d3e3b5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4d3e3b587a64ebe2c84584187c3d2510a88ff24d))
* use .is_(True) and add or 0 guards per code review ([2b3587d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2b3587d7ab65e2c5d2f1780f2b8fe499c2ba7ba4))
* use direct is_trial access, add missing error codes to promo APIs ([dc49252](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc49252e5a3b556eeeea473034d4ceffa05bec07))
* use float instead of int | float (PYI041) ([978a8e0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/978a8e0ead8737c39fe27a4be2195228bf3a7cd0))
* use SAVEPOINT instead of full rollback in sync user creation ([48e4417](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/48e441759e2d33a94e30aae62c6446f3ca9436e5))
* гарантировать положительный доход от подписок и исправить общий доход ([0563786](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0563786797d1269c305af873b15e431defe73b48))
* добавить create_transaction для 6 потоков оплаты с баланса ([ec56f96](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec56f96e2c218573897608ee17e6d2c196de5991))
* добавить create_transaction и admin-уведомления для автопродлений ([10dd6ac](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/10dd6ac7a6bfeaaf84e8394b4fde0b53e0ba16b0))
* добавить пробелы в формат тарифов (1000 ГБ / 2 📱) ([390b943](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/390b943a2549c96f2b8ea5ac9b4b590be94831cf))
* дубликаты системных ролей при переименовании и сброс permissions ([01ce477](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/01ce4771bd9b3bba44be8ed5cbcc5f25654275dd))
* изолировать stored_amount от downstream consumers в create_transaction ([af7ee03](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/af7ee032689a3eb8cac95e2b06bb51749a6588b8))
* исправления системы реферальных конкурсов ([be7d626](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/be7d626eea0a192524f83a29389ffb67a1b4e704))
* кнопка «Назад» в тарифах ведёт в админ панель, а не в настройки ([0bd792d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0bd792defdc345a5b495c742caf60335e472c856))
* передать явный диапазон дат для all_time_stats в дашборде ([a7ee6ca](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a7ee6cade637b2ea17d80084b73be5daa44841d8))
* показывать кнопку покупки тарифа вместо ошибки для триальных подписок ([7dc9f46](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7dc9f46ec6f897e8c873d71d7e8059a53aede14f))
* промокоды — конвертация триалов, race condition, savepoints ([e9ce548](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e9ce548c8495624f5fcb2d578546ca599526526f))
* реактивация DISABLED подписок при покупке трафика для LIMITED пользователей ([49e5a14](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/49e5a141a474ada8e6aabc774b438b196b9b0f68))
* реактивация DISABLED подписок при покупке устройств и в REST API ([7c0ce3f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7c0ce3f028415a5ff871d6f4aa94ffc351e68119))
* синхронизация версии pyproject.toml с main и обновление uv в Dockerfile ([7df5940](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7df59401c55363b74eb7469c7fc2e9a758738c1d))
* убрать WITHDRAWAL из автонегации, добавить abs() в агрегации, исправить all_time_stats ([53714ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/53714ae5d757d07766defb960d417a005465c069))
* убрать избыточный минус в amount_kopeks для create_transaction ([f81439a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f81439a3849ec63315a73b520c490bef53162775))
* устранение race condition при покупке устройств через re-lock после коммита ([ede87ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ede87eeb126d6dd89c5ba0463d245bfd310bcdf2))
* устранение race conditions и атомарность платёжной системы ([8351ab1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8351ab1e21a42a3bcae3a3e928eae4b239fb2bfc))
* устранение каскадного PendingRollbackError при восстановлении бэкапа ([6d7688c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6d7688c4f172955b0012057ecd8e54289dd46f50))


### Refactoring

* complete uv-only dependency workflow ([b1ad9ff](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b1ad9ff314489651acabf24924b06e60c030b9bd))

## [3.22.4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.22.3...v3.22.4) (2026-03-01)


### Bug Fixes

* **updates:** pin telegram update checker to fork repository ([23d6814](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/23d681429a1b5783df752a373fd13ef16f239b7f))

## [3.22.3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.22.2...v3.22.3) (2026-03-01)


### Bug Fixes

* **cabinet:** add menu layout reset endpoint ([f5da309](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f5da30989e0a547b77720a0eff481525c47e004d))
* **menu-layout:** allow unknown condition keys in schema ([64895d1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/64895d1d8a433e2f081dd0526966ca745d1c727e))
* **menu-layout:** keep buy button visible for active users in tariffs mode ([d7326f3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d7326f333440985b200a2b39e67c542f223f80d6))

## [3.22.2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.22.1...v3.22.2) (2026-02-28)


### Bug Fixes

* **updates:** enforce PEDZEO repos in admin releases endpoint ([08ef64a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/08ef64ac920cc4dbe06cfb7c3c641239aec371c4))
* **updates:** use PEDZEO cabinet repository for release links ([94deff3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/94deff3551f70a45dfc315d9cef13e3fbfe1ef3a))

## [3.22.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.22.0...v3.22.1) (2026-02-25)


### Bug Fixes

* **ci:** make mypy checks pass locally and in workflow ([96d9116](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/96d9116ee466e2827a3ccdd8e1e68680b972d3bd))
* make migrations 0010/0011 idempotent, escape HTML in crash notification ([fd6b6ea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fd6b6eae49d70b6c09b49ae77c46c99ed532f8c1))
* prevent race condition expiring active daily subscriptions ([145f39d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/145f39d9b87fdaecab4fac6a34e98658c5ddb6af))
* **types:** resolve mypy issues in external and utils modules ([bf9cbcc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf9cbcc0276decb9d808eb351344746ecb735126))


### Documentation

* clarify fork differences for users ([8a46a9b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8a46a9bbd1a0d8ca63740ede5525fcba9a5ec1da))
* remove fork audience section ([e813803](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e8138036bf331e649ad8ad2bd53dbcc2696c41ec))
* update test bot and contact handles ([9f69726](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f6972635162172cf4de3b1cff2dcf6492131900))

## [3.22.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.21.0...v3.22.0) (2026-02-25)


### New Features

* add admin balancer endpoints for cabinet ([ff2f721](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff2f7212160197661d2fac495bb56a79bb13958a))
* add granular user permissions (balance, subscription, promo_group, referral, send_offer) ([60c4fe2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/60c4fe2e239d8fef7726cac769711c8fcce789eb))
* add per-channel disable settings and fix CHANNEL_REQUIRED_FOR_ALL bug ([3642462](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3642462670c876052aa668c1515af8c04234cb34))
* add RBAC + ABAC permission system for admin cabinet ([3fee54f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3fee54f657dc6e0db1ec36697850ada2235e6968))
* add resource_type and request body to audit log entries ([388fc7e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/388fc7ee67f5fc0edf6b7b64b977e12a2d8f0566))
* add separate Freekassa SBP and card payment methods ([0da0c55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0da0c5547d0648a70f848fe77c13d583f4868a52))
* add validation to animation config API ([a15403b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a15403b8b6e1ec1bb5c37fdde646e7790373e860))
* allow editing system roles ([f6b6e22](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f6b6e22a9528dc05b7fbfa80b63051a75c8e73cd))
* **cabinet:** proxy balancer quarantine admin endpoints ([9f67e21](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f67e2127557b85c31e51589ee8bba0b9fa40de8))
* capture query params in audit log details for all requests ([bea9da9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bea9da96d44965fcee5e2eba448960443152d4ea))
* proxy balancer groups management endpoints ([2ff2a3f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2ff2a3f63561a0a8c784c322b6653ba798543aa4))


### Bug Fixes

* address RBAC review findings (CRITICAL + HIGH) ([1646f04](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1646f04bde47a08f3fd782b7831d40760bd1ba60))
* align RBAC route prefixes with frontend API paths ([5a7dd3f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a7dd3f16408f3497a9765e79a540ccdabc50e69))
* always include details in successful audit log entries ([3dc0b93](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3dc0b93bdfc85fb97f371dc34e024272766afc65))
* **auth:** restore optional telegram identity validation ([38a7029](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/38a7029e044c1486ba62da54a39af94b3f43eb97))
* **backup:** add missing settings app config path getter ([0d6c670](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0d6c67092614da4e8f2d04e63307e0b60b6e5ded))
* **cabinet:** sort route imports for ruff ([04cd4cf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/04cd4cf51f929bcf01884f487626794d85641127))
* **cabinet:** switch balancer proxy to admin endpoint namespace ([4544910](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/454491056cde3af1a67520ae6a089df6a9ab84e2))
* extract real client IP from X-Forwarded-For/X-Real-IP headers ([af6686c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/af6686ccfae12876e867cdabe729d0c893bd85a1))
* grant legacy config-based admins full RBAC access ([8893fc1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8893fc128e3d8927054f1df1647e896e780c69e7))
* improve campaign notifications and ticket media in admin topics ([a594a0f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a594a0f79f48227f75d6102b4586179102c4d344))
* initialize logger in bot_configuration.py ([988d0e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/988d0e5c2f27538135d757187a0b6770f078b1d9))
* **miniapp:** correct helper schema relative imports ([16682ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/16682ef809aaaf6a300c5b592a129ccada4af36f))
* **miniapp:** correct payment helper schema import path ([21c4242](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21c4242cd22d159d3818913327022233bcc3054d))
* **miniapp:** correct renewal payment cryptobot helper import ([48e3871](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/48e3871cf8a52707c581daf7081c7e0cf788fc57))
* **miniapp:** restore test compatibility after helper split ([f202586](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f202586366224c6522172e27d613f09af41376a0))
* normalize remnawave mutable user statuses ([f439cef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f439cef8c2778b357c3e12675c62a2a98edcc6a8))
* RBAC API response format fixes and audit log user info ([4598c27](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4598c2785a42773ee8be04ada1c00d14824e07e0))
* RBAC audit log action filter and legacy admin level ([c1da8a4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c1da8a4dba5d0c993d3e15b2866bdcfa09de1752))
* remove gemini-effect and noise from allowed background types ([731eb24](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/731eb2436428d0e12f1e5ccdebc72cd74fd7c65e))
* resolve ruff lint errors (import sorting, unused variable) ([b2d7abf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b2d7abf5bd10a98fd7ad1da50b5072afc65a5b48))
* resolve sync 404 errors, user deletion FK constraint, and device limit not sent to RemnaWave ([1ce9174](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1ce91749aa12ffcefcf66bea714cea218739f3fe))
* restore post-merge model imports and device limit handling ([7a98eed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7a98eed275884a8766f11ea5e26d706d0bf98bac))
* restore subscription_url and crypto_link after panel sync ([26efb15](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/26efb157e476a18b036d09167628a295d7e4c10b))
* specify foreign_keys on User.admin_roles_rel to resolve ambiguous join ([bc7d061](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bc7d0612f1476f2fdb498cd76a9374b41fd9440a))
* stack promo group + promo offer discounts in bot (matching cabinet) ([628997f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/628997fb48413cc4fae9ac491d1c7f6185877200))
* wire cabinet rbac routes ([3997dbb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3997dbb710b99683d9f5ad39db27790b50e16607))

## [3.21.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.20.0...v3.21.0) (2026-02-24)


### New Features

* add ChatTypeFilterMiddleware to ignore group/forum messages ([c9b4247](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c9b4247af2c37f8ed6cab58ed797363b4d925242))
* add ChatTypeFilterMiddleware to ignore group/forum messages ([25f014f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/25f014fd8988b5513fba8fec4483981384687e96))
* add multi-channel mandatory subscription system ([0420237](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/04202379dbd0eb357323b77c518d2d891d52cbce))
* add multi-channel mandatory subscription system ([8375d7e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8375d7ecc5e54ea935a00175dd26f667eab95346))
* add required channels button to admin settings submenu in bot ([4944568](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/494456837692cb3bf6645b0912c6d253a1147833))
* add required channels button to admin settings submenu in bot ([3af07ff](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3af07ff627fc354da4f8c41b0bd0575dddd9afa5))
* **cabinet:** add menu layout stats endpoints ([4ea3c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4ea3c5f87e4562f40eb20bb7361f72e201953025))
* colored channel subscription buttons via Bot API 9.4 style ([343bfcd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/343bfcd18435803cd17eeef4be0ebdb584dfa102))
* colored channel subscription buttons via Bot API 9.4 style ([0b3b2e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b3b2e5dc54d8b6b3ede883d5c0f5b91791b7b9b))
* rework guide mode with Remnawave API integration ([5a269b2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a269b249e8e6cad266822095676937481613f5f))


### Bug Fixes

* add diagnostic logging for device_limit sync to RemnaWave ([b6b91fb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6b91fb3b8a736cd59bb488fba9fd4d0827954d8))
* add diagnostic logging for device_limit sync to RemnaWave ([97b3f89](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97b3f899d12c4bf32b6229a3b595f1b9ad611096))
* add int32 overflow guards and strengthen auth validation ([50a931e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/50a931ec363d1842126b90098f93c6cae47a9fac))
* add missing broadcast_history columns and harden subscription logic ([d4c4a8a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d4c4a8a211eaf836024f8d9dcb725f25f514f05e))
* add missing CHANNEL_CHECK_NOT_SUBSCRIBED localization key ([66644de](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/66644defdf98e263537c0ab05f070dff957970b1))
* add missing CHANNEL_CHECK_NOT_SUBSCRIBED localization key ([a47ef67](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a47ef67090c4e48f466286f7c676eeee0c61a4fb))
* address code review issues in guide mode rework ([fae6f71](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fae6f71def421e319733e4edcf1ca80a2831b2ec))
* address security review findings ([6feec1e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6feec1eaa847644ba3402763a2ffefd8f770cc01))
* allow tariff switch when less than 1 day remains ([167919d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/167919d0aa4d87e9211310a70f799f550d2e5024))
* allow tariff switch when less than 1 day remains ([67f3547](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/67f3547ae2f40153229d71c1abe7e1213466e5c3))
* callback routing safety and cache invalidation order ([6a50013](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6a50013c21de199df0ba0dab3600b693548b6c1e))
* cap expected_monthly_referrals to prevent int32 overflow ([3173905](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3173905bd1da9caf1955e936d75d4709b4971cd0))
* cap expected_monthly_referrals to prevent int32 overflow ([2ef6185](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2ef618571570edb6011a365af8aa9cd7e3348c2e))
* correct broadcast button deep-links for cabinet mode ([9ff3929](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ff3929f1092948af0f55dd2faecfb4acd9070af))
* correct broadcast button deep-links for cabinet mode ([e5fa45f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e5fa45f74f969b84f9f1388f8d4888d22c46d7e8))
* cross-validate Telegram identity on every authenticated request ([ff8ca98](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff8ca98e32950a0165c1e1df8ba70449a3b830eb))
* cross-validate Telegram identity on every authenticated request ([973b3d3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/973b3d3d3ff80376c0fd19c531d7aac3ae751df8))
* handle RemnaWave API errors in traffic aggregation ([4fc6aee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4fc6aeeb5f9d09b2bf8951cffb40704bc56b2085))
* handle RemnaWave API errors in traffic aggregation ([ed4624c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ed4624c6649bdbc04bc850ef63e5c86e26a37ce4))
* HTML-escape all externally-sourced text in guide messages ([711ec34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/711ec344c646844401f355695a7e8c0d4fb401ee))
* improve deduplication log message wording in monitoring service ([e0412aa](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e0412aa80c0b8c3d59d9671a312009d72d6b76c8))
* improve deduplication log message wording in monitoring service ([2aead9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2aead9a68b6bf274c8d1497c85f2ed4d4fc9c70b))
* invalidate app config cache on local file saves ([978726a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/978726a7856cf56257c49491afe569fa8c395eac))
* migrate all remaining naive timestamp columns to timestamptz ([708bb9e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/708bb9eec7ea4360b26709fb2a3f82dd139ed600))
* pre-existing bugs found during review ([1bb939f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1bb939f63a360a687fafba26bc363024df0f6be0))
* prevent partner self-referral via own campaign link ([3c6552f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3c6552fc92022d13a45e40db98fd91fb7b6be67c))
* prevent partner self-referral via own campaign link ([115c0c8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/115c0c84c0698591da75d7d3b8fbd8e0fc8541ea))
* protect active paid subscriptions from being disabled in RemnaWave ([1b6bbc7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1b6bbc7131341b4afd739e4195f02aa956ead616))
* remove [@username](https://github.com/username) channel ID input, auto-prefix -100 for bare digits ([512010a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/512010a6c9d871aa9898d22e1e0ab8b41cedf9a7))
* remove [@username](https://github.com/username) channel ID input, auto-prefix -100 for bare digits ([a7db469](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a7db469fd7603e7d8dac3076f5d633da654a3a57))
* repair missing DB columns and make backup resilient to schema mismatches ([c20355b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c20355b06df13328f85cc5a6045b3e490419a30a))
* restore RemnaWave config management endpoints ([6f473de](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6f473defef32a6d81cee55ef2cd397d536a784a7))
* show negative amounts for withdrawals in admin transaction list ([21c3a01](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21c3a016b3fdeac85d21cebbabe61188400be904))
* show negative amounts for withdrawals in admin transaction list ([5ee45f9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5ee45f97d179ce2d32b3f19eeb6fd01989a30ca7))
* suppress web page preview when logo mode is disabled ([edff3d8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/edff3d851735d4212e8fd807a542a9d0ee836180))
* suppress web page preview when logo mode is disabled ([1f4430f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f4430f3af8f3efcc58ef7b562904adcb1640a44))
* translate required channels handler to Russian, add localization keys ([bf83509](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf835094cab92c4dc5a2933df3d915a8ff338462))
* translate required channels handler to Russian, add localization keys ([1bc9074](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1bc9074c1bcdaba7215065c77aac9dd51db4d7c8))
* uploaded backup restore button not triggering handler ([ebe5083](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ebe508302b906f8b56cb230b934fb8566990c684))
* use aiogram 3.x bot.download() instead of document.download() ([16b10fd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/16b10fd4fc412a797476b713c1c8692bd02b21fc))
* use aiogram 3.x bot.download() instead of document.download() ([205c8d9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/205c8d987d93151a17aa0793cb51bd99917aea97))


### Refactoring

* **miniapp:** centralize subscription update finalize flow ([cd33859](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cd33859b91b67ad91cc3f712b3733a63c8961f7e))
* **miniapp:** centralize tariff switch pricing and messages ([428ea1d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/428ea1decf49e660a4d5af7aec0a76345b17aa0f))
* **miniapp:** extract auth helper module ([2d60f75](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2d60f75233129c50b3c3d9b42d2cdf85391fe42d))
* **miniapp:** extract autopay helper functions ([e313cc5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e313cc5b169aa426fe82f5d44cc272fc7009e139))
* **miniapp:** extract cryptobot helper module ([6ab7124](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6ab71246a12c7e209a2af58510a19212156d867d))
* **miniapp:** extract daily subscription toggle helpers ([69220cc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/69220ccf31316870a0848048d09cd71ffc9afd08))
* **miniapp:** extract datetime format helper ([b5f2d74](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b5f2d74c4d956d4ccacccb4019e55ab1da087d8b))
* **miniapp:** extract misc helper module ([6040065](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6040065bd1c87acbb8e131fcee868fbe068045a1))
* **miniapp:** extract payment amount helper module ([7944f9e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7944f9e53a9fafc91fe4b9c99441de419b140948))
* **miniapp:** extract payment create input and cryptobot handler ([adcfe01](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/adcfe010e76ce1c72f6fc62c00d85946f9559150))
* **miniapp:** extract payment lookup helper module ([8bd6796](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8bd679662c338a7f085cc19d3754bd00a4194ca2))
* **miniapp:** extract payment method status helpers ([87127de](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/87127ded2a94e0b6851c65484303eb96addb83a9))
* **miniapp:** extract payment request helpers ([df7d6a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/df7d6a898631ee235fb0803077972bb228ac907f))
* **miniapp:** extract payment status classification helper ([16a77ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/16a77ee1f500b060f0cc71eb6c8098f2ebe31534))
* **miniapp:** extract pending payment status builder ([291cdff](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/291cdff6fec3ccc389d414a632a95b8d8b05f644))
* **miniapp:** extract promo discount helper module ([1915ccf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1915ccf235af7e3e317afb382a78c21d6bb36bff))
* **miniapp:** extract promo offer helper module ([d548fa4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d548fa47b23d458be95aa6dc992c1f514401b9a0))
* **miniapp:** extract purchase selection helper ([a6b7b59](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a6b7b59a58edf319a219a69c4767cca60865f181))
* **miniapp:** extract renewal message helper module ([c81486c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c81486c799cb38e940d0f81fb2736b69b384e598))
* **miniapp:** extract renewal submit parsing and payment helpers ([281a90c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/281a90c1e7aefb74c5c981e32b38ba63263844d2))
* **miniapp:** extract shared formatting helper module ([aa85093](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa85093ecb9a6ddf1ce388f843023da9cc2391fa))
* **miniapp:** extract subscription devices update logic ([9f7eaec](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f7eaec6ae02225f07f973e4191b157195ebc7b9))
* **miniapp:** extract subscription helper module ([3345b4a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3345b4a0b3389f6ba72f7a51a47f8ef5750b4a1d))
* **miniapp:** extract subscription servers update planning and apply flow ([5e1e7d1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5e1e7d19c82f7ccc78d7c02b029112f9c89c8fc5))
* **miniapp:** extract subscription traffic update logic ([dab20a2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dab20a260dbde994dcb5473b1977430844e643d9))
* **miniapp:** extract tariff helper module ([e598e9e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e598e9ea1d0d8930dc3addcdd60a66ceedb3c3a2))
* **miniapp:** extract tariff purchase context and balance checks ([a3d1464](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a3d14644178066a3c06dae8f56f6839ebf504090))
* **miniapp:** extract tariff switch pricing helpers ([29f9fb4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/29f9fb4a2cb3cbe4ffe88dd81a90c1361221253d))
* **miniapp:** extract tariff switch validation context ([9249b70](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9249b70482fb8f60c648fe7d77078a98a3a38521))
* **miniapp:** extract unknown payment status builder ([d41a107](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d41a107408f26113eac193a1cf4e767d4fe22586))
* **miniapp:** extract yookassa payment create handlers ([a3365bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a3365bd379635d6f8e2326b9f190fc60dfd37a36))
* **miniapp:** group payment helpers into payment package ([b7e057c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7e057c6df454dc23ce3db2a0cec4bbe0a503305))
* **miniapp:** group promo helpers into promo package ([44670f9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/44670f9b55d866e017b60adc3369c38711db0d58))
* **miniapp:** group subscription and tariff helpers into packages ([d445e27](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d445e2743f2c4ba607f7e7eed0c4072129ee3fd0))
* **miniapp:** move base payment status resolvers to module ([551f443](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/551f443d1ea07a479b77cdd7bc842637598c5295))
* **miniapp:** move daily resume remnawave sync to helper ([c2ed68d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c2ed68de4c022ce7c58c5c4c15685bf146169cdb))
* **miniapp:** move direct payment status resolvers to module ([2ea9ab8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2ea9ab8721143fc236d3e00cdc04776599fbec56))
* **miniapp:** move gateway payment status resolvers to module ([2179dea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2179deabf3e538a43d634468db1625b2f5193b03))
* **miniapp:** move init-data user resolver to auth helper ([efe20df](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/efe20dfb1e498d2d3fe85f97b48f5d20b8d58334))
* **miniapp:** move payment status dispatcher to module ([b226242](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b226242157c61d1efab2e86810b5c2f3447e704f))
* **miniapp:** move promo offer model builders to module ([ca7e761](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ca7e76183bf789b84dbea645b3765d7d17436ced))
* **miniapp:** move referral info builder to module ([c89028f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c89028f345889e8b225f177d7ffddb7adffbd8c8))
* **miniapp:** move renewal cryptobot flow to helper ([1063c88](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1063c885ea3bcd66c95032fafcf6409293675ae7))
* **miniapp:** move renewal execution paths to helpers ([c7acbeb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c7acbeb77c1a934f3e34ba773d179665c55306be))
* **miniapp:** move renewal options builder to helper ([5ffeefa](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5ffeefa1dfb613515d24bdc919d43d2ffb0508a3))
* **miniapp:** move subscription runtime helpers to module ([eddabe4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eddabe47d0686bfe2a31441e0be3d605d2c35b07))
* **miniapp:** move subscription settings builders to helper ([feb59d1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/feb59d1d434fe3822b94370b796d0fdba680e225))
* **miniapp:** move tariff api model builder to helper ([503b590](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/503b59032eabc19f4b85d93fcf5c4b20858bd455))
* **miniapp:** move tariff switch charge transaction flow to helper ([c39e26e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c39e26e20f512277959ce3c833a7f7d794885a7c))
* **miniapp:** move tariff switch subscription mutation to helper ([1f06806](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f06806f77c7b6013583e619414fd2e3e03c1fde))
* **miniapp:** move tariffs endpoint payload assembly to helper ([76d2d55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/76d2d551482b9f29a311fd4aca9e3ad919871462))
* **miniapp:** move traffic topup execution flow to helper ([1da3d32](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1da3d321881d5b55c972872a50140be2d08a5079))
* **miniapp:** move traffic topup validation and pricing to helper ([dc7b863](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc7b8634328893f3ec9051e103e55585a71c68cc))
* **miniapp:** move trial and current tariff state helpers ([6140651](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6140651f100ed47cf7e16c63a745a77a8122e70d))
* **miniapp:** organize helpers into miniapp_helpers package ([3d22800](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3d22800e72e580f449de3011334a2401226c7803))
* **miniapp:** reuse pending status helper for pal24 ([1cb17b2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1cb17b22b3e7b925a4a0c40713d5e5eda0e54aa6))
* **miniapp:** reuse pending status helper for platega and wata ([2c655cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2c655cb8d1d060d23a59618833c41eb3d5a5d17d))
* **miniapp:** reuse shared tariff squad resolver ([f813e34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f813e345bb267e4572acb418ea8b2eca070f7f71))
* **miniapp:** unify tariffs-mode guard via helper ([8378064](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8378064fa45767029aa9cd6f92d41c5f0561e0a7))
* remove legacy app-config.json system ([295d2e8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/295d2e877e43f48e9319ba0b01be959904637000))
* **subscription:** extract app-config deep-link helpers ([c0789b3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c0789b374baaea2c89b7c5f22e265ead6cfe5782))
* **subscription:** extract shared route helpers module ([d78a9db](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d78a9db134f3e381a8d5f434cca2c5ae72b361d1))

## [3.20.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.19.0...v3.20.0) (2026-02-22)


### New Features

* brand admin alerts for PEDZEO fork ([cec8257](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cec82571866fbf6667395c024d8cf109b67e1efc))


### Bug Fixes

* avoid button click FK race on user lookup ([1f814a6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f814a6cff2031a2ce788a6c9b2aded4e9d1d655))
* close async teardown leaks and re-enable unraisable checks ([3014332](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/301433227e7905c0a6764721daa269fb55e80780))
* fallback button click log to null user on FK conflict ([3982bd4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3982bd40b76074e86ebd3c467a2fccead2b32f9e))
* lock user row before button click stats insert ([818ac96](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/818ac960f612100236bf8a32ed0e277f30114064))
* log callback button stats without user FK dependency ([ee7be0f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ee7be0f7f1353fb78cb7a1cb8c6348bacc5eea67))
* **menu-layout:** apply cabinet button styles in layout mode ([ea10a2c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ea10a2c5b12b9c200021cead0fb10eef9b2ea282))
* **menu-layout:** disable style when section is off ([c08b458](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c08b458e6f80e56335ecc4f917d45af4f20c9eb6))
* point update notifications to PEDZEO repo ([564b07a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/564b07a60e9647f0f321b4bf6f07f731a79485d3))
* remap legacy alembic revision before upgrade ([e0f030e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e0f030e843be39a62f9ae512a18d8241e341fe76))
* stabilize tests and suppress legacy warning noise ([b873019](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b8730191a75541ca7fbdedecfdb3defb2111c9aa))


### Refactoring

* add explicit bootstrap service startup types ([1e5ab51](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e5ab515e3f7c1733e540ab0827d44c573a122c4))
* add explicit return type for runtime logging setup ([41932d5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/41932d5740268ffbccbb3cbc28c27692453f71da))
* add explicit return type for top-level main ([34f270d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/34f270d020d21bf5332b699294b888fa17bbdc7c))
* align settings model_config with pydantic v2 API ([9144a4a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9144a4a01477b5b855d95377f83950565103b5cd))
* **bootstrap:** extract backup startup stage ([9f4a8dd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f4a8dde5102dd552741e371eb53dc9c37ac816f))
* **bootstrap:** extract bot setup stage ([b7aad31](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7aad313e2ffada6147a2dabc0d6704a53a636fd))
* **bootstrap:** extract configuration loading stage ([938e27e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/938e27edad298e070e6bdcb11a2e90350597b96f))
* **bootstrap:** extract contest rotation startup stage ([3068c50](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3068c50f4d4166cc4f07a9e1e4823362656dafd4))
* **bootstrap:** extract core runtime startup pipeline ([8ba89a1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8ba89a1defd1745d189ee08bd436dc4908b1ce01))
* **bootstrap:** extract daily subscription startup stage ([c57ae80](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c57ae806b38551ad4d5b092bbd8cc6225c70a95f))
* **bootstrap:** extract database initialization stage ([2c5bb92](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2c5bb92ac7195480af51a0f74d0300d8e9cdf363))
* **bootstrap:** extract database migration startup stage ([6d7d2a4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6d7d2a4c2369f42f3aa685d268f8fae9a0f50ba2))
* **bootstrap:** extract entrypoint crash handling ([658a4ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/658a4ae54453ed177a1fc97e91449eee900ae62f))
* **bootstrap:** extract external admin startup stage ([8416b01](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8416b0156bff39be6203329c80050449cb5074d6))
* **bootstrap:** extract graceful signal handlers ([84b47f4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/84b47f473b85093c25e420d53253d76ee456b312))
* **bootstrap:** extract localization startup stage ([8074929](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/80749294291b919498a442e7ff38820e77abfdce))
* **bootstrap:** extract log rotation startup stage ([c6ecb4b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c6ecb4b4a2407257a3516ec59db60c62641eee17))
* **bootstrap:** extract maintenance startup stage ([5b9c53a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5b9c53a46e83a280cfb63dbaf738e9f524c9a58a))
* **bootstrap:** extract monitoring startup stage ([ed05eab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ed05eabbb9237dad4ff8362a835a0de54471421c))
* **bootstrap:** extract nalogo queue startup stage ([6af3ba6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6af3ba66166e82073ebf4debd1d17539161441d0))
* **bootstrap:** extract payment methods startup stage ([7209097](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7209097cba82d0df0e6769409d3f5a03f1bcf900))
* **bootstrap:** extract payment runtime setup ([1c58232](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1c58232f511290707a0b6395677baa9ac97a1aec))
* **bootstrap:** extract payment verification startup stage ([62068c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/62068c58f7d76afc830f731a5a2aa447810012d2))
* **bootstrap:** extract polling startup stage ([ebca928](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ebca92862ccc186870a04ba48fd12d2e8bbef7ba))
* **bootstrap:** extract referral contests startup stage ([a413cc8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a413cc8fdb9e948c110f62cce6d9a92adfd6ebce))
* **bootstrap:** extract remnawave sync startup stage ([4945448](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4945448ab85045bd47aa4777ee9ec90fa20878c4))
* **bootstrap:** extract reporting startup stage ([6835028](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/683502868f78008ffc7215be3646c43b9c195e27))
* **bootstrap:** extract runtime execution stage ([74e59e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/74e59e5f4fa59a5e7d77e2cfcc5aefccf8d62271))
* **bootstrap:** extract runtime logging configuration ([9ce92d2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ce92d285a9d1e041b9d08623ff5cd82c79cb723))
* **bootstrap:** extract runtime logging configuration ([c499f40](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c499f40d205950d73623f9c8cbc6906ed4f7aaa2))
* **bootstrap:** extract runtime mode resolution ([97d7e9b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97d7e9bdfe049bf3ffdeb3cc80bc540b15f51a05))
* **bootstrap:** extract runtime services shutdown stage ([6c9df32](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c9df32536673a830aa7905e1ac096bf7826e172))
* **bootstrap:** extract runtime tasks startup stage ([43aa907](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43aa907f98b1636aec6c5f959557f42524475e4c))
* **bootstrap:** extract runtime watchdog loop ([532c9a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/532c9a87d12936eb78b83db65a03e089ef98e326))
* **bootstrap:** extract server sync startup stage ([9bc7300](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9bc730027b87171fd3b813f8111a87ce11b7aa74))
* **bootstrap:** extract service wiring stages ([4893ebe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4893ebee177fd018313b03963f95a17ab026922a))
* **bootstrap:** extract shutdown pipeline ([a8bef70](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a8bef7028ce2dd9a949166f2ab33d209a13eb3e9))
* **bootstrap:** extract startup finalize stage ([40ea967](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/40ea967d2016aa6278c56640ea95c389bdc04e90))
* **bootstrap:** extract startup notification sender ([09b4bf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/09b4bf536999dea27012a311845b62d168e21d86))
* **bootstrap:** extract startup summary logging ([8142da7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8142da78c839d5fe2d471914f4225870a9845396))
* **bootstrap:** extract tariff sync startup stage ([924278f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/924278f08585cf2a93cd22038229a478702b691e))
* **bootstrap:** extract telegram webhook startup stage ([284f05a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/284f05a07ba777fc64ad2519f5cd841aaba01a81))
* **bootstrap:** extract traffic monitoring startup stage ([812d1ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/812d1ef3f2cfb1b1c71bacc197c5c5cd11303bad))
* **bootstrap:** extract version check startup stage ([5c485c8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5c485c8bc3207dfa5d405ea55f7beaaad94a27b0))
* **bootstrap:** extract web server startup stage ([24f28a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/24f28a897c2aced90b3ee4748376a9ea65a7d4bd))
* **bootstrap:** extract web shutdown stage ([569768c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/569768cb1287f2a91ecddae186fd245be3600ca0))
* **bootstrap:** tighten runtime typing contracts ([4b0ffca](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4b0ffcaf62c8a2285f9d74f1307105b0cbbbd464))
* centralize runtime state mappings ([3a036f5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3a036f5d99b62cb36f8a423cd67547680d9d5bfe))
* centralize runtime task assembly ([52bb959](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/52bb959312469b55ed7138447aced56bb065af54))
* centralize shutdown payload assembly ([b7629cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7629cb4ae4ba16d233f986069cffc8f543ee038))
* centralize startup summary payload mapping ([c273f8e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c273f8eab276e1fc54dd397c1af52b6b3cd1f113))
* complete startup stage error helper rollout ([c3462fc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c3462fc2a76a59b025624ab6aaff8dca2e53045d))
* deduplicate core payment CRUD wrapper calls ([4630f0a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4630f0a78192c9b4aad72b63b1fcc36572f9189d))
* deduplicate runtime shutdown stop calls ([0cd70eb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0cd70eb3b20edafde68ad8e1cd69880eb11142bd))
* deduplicate runtime watchdog restart branches ([026bdf6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/026bdf6775e471f3073b355e7a9a55130772b5cd))
* extract alembic revision read helper in migration bridge ([62627ea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/62627ea41f6721d14dcb0f919cc3bcab961a78a4))
* extract preflight runtime object builder ([00693bb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/00693bbd55a3d7499728395c57c709b34577372b))
* extract runtime preflight banner metadata builder ([499ff9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/499ff9a328d46cc61a0a81903b233cb1c1fef977))
* extract runtime preflight bootstrap ([5c6a1ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5c6a1eef48cf9b0d5ee27a5a95a3e43d39162aae))
* extract runtime session flow ([26509f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/26509f236efa327f74f2ea6e17e50eb504c0c398))
* extract runtime shutdown payload composer ([86c1e17](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/86c1e17cb1bd65e6b323f2b99e16ac69966c7406))
* extract startup runtime orchestration ([7f8ca2b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7f8ca2b44d0bc23633b6d8d7d14da274a7ebea1d))
* formalize core runtime mode flags contract ([0c6a711](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c6a711fc87d80baf0751a150f86d8f9b25bb97d))
* generate payment CRUD compatibility wrappers ([e61bdc4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e61bdc48a1a22d8554b00939799b15237a9978f1))
* group guarded service shutdown calls ([a98127f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a98127f3a09bd08635449422c240b2feae129b12))
* isolate core runtime context assembly ([c8b45c0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c8b45c001baaf4a621e01ab90921d2e9bab001c0))
* isolate post-payment bootstrap sequence ([72a6bc4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/72a6bc4e4475cc852aeb0ca0680f19b5d1c2829b))
* isolate pre-runtime bootstrap sequence ([e484970](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e48497036b36221f10d3a92f75f452ddafb96d21))
* isolate runtime loop state handoff ([708662c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/708662c315797d475d661e8253be8710ed909472))
* isolate runtime orchestration task startup handoff ([c288a1a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c288a1a12b7a427668635cec8934cf20a1c821af))
* isolate runtime session shutdown finalization ([d026142](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d026142d6a6b290e2df1843c1447dbc0ce035abd))
* isolate runtime shutdown args builder ([edaec72](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/edaec727650910f47f1a67879f0931f0acd41513))
* isolate startup finalize args builder ([86012c0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/86012c06b200ed38a4563ffecdd74add6e212a03))
* isolate web shutdown args builder ([5821db5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5821db5d0c9cafceeb98a3347c20fdeaa0f054d1))
* isolate web startup bootstrap sequence ([bcf4361](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bcf4361b3c570d0e174e57f5a274ae4f9c1d6ee8))
* **main:** extract runtime state container ([147b033](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/147b0331495a59ecb081c9d6f520295dda830671))
* **main:** remove locals check for bot shutdown ([e1d5748](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1d57488f5c7e4a3b9f0db87d3321a9a2957fd55))
* migrate admin and webhook schemas to pydantic v2 config ([429f40b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/429f40be0cab6af78f7ec44946cd75de7cc838a5))
* migrate campaign schema validators to pydantic v2 ([6a19c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6a19c5f2c2571cb533ad20d29d922c56cd71408a))
* migrate common webapi validators to pydantic v2 ([0b0b449](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b0b449dc0f1e7ef0a33623482d2faa17d0b5dcc))
* migrate core cabinet schemas to pydantic v2 config ([7ad8f0d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7ad8f0d834302c1ed622f29f0700dd5e5d6e5c4e))
* migrate promo and broadcast validators to pydantic v2 ([5a87908](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a879081203feda9358827e3b2e14d4ec8ca5e1a))
* migrate remaining cabinet schemas to pydantic v2 config ([183eb67](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/183eb675cc52622e8b69dff892cfc97b3f3fc1c5))
* migrate unified app lifecycle to lifespan ([5ba3ea8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5ba3ea809f6a6f2df5703ad3494b2babaab9fb77))
* migrate webapi payload serialization to model_dump ([b54bb88](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b54bb88d3ac5d7fe7002725c0a3477558f541c20))
* reduce pydantic and async-test warning hotspots ([e841d72](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e841d727f17de56a5d9d2f9c86dd0d39a3cd1684))
* reuse startup error helper in service stages ([21bd8db](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21bd8db938b11851822eb7a1a6b0b542180dc825))
* share startup stage error handling ([b6e2ed7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6e2ed7ed80bee827d1e54cdc9aa26addd1bd025))
* simplify migration startup flag handling ([328a6a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/328a6a875dde0809d25a9f0c5675ec58afb2c543))
* simplify startup webhook summary assembly ([cb44fb9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cb44fb948d31567ca23702952653d42034429fb9))
* split shutdown pipeline stage dispatch ([1a5ff6f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1a5ff6f421f3fa6c4072c8b8d54ac3ff83c77fbb))
* tighten bootstrap entrypoint coroutine contract ([78e1a34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/78e1a341b4b4fc8f52f07df463adae31121984d6))
* tighten bootstrap logger and notifier protocols ([eff907d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eff907df5c9782a78ba00dbb26645315fbf23331))
* tighten bootstrap web shutdown typing and pytest loop cleanup ([4d907ed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4d907edea2b9ab2b536c587b6c61086e19fdb3c2))
* tighten runtime orchestration typing ([df59285](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/df592852ad955dee83bbb2192211d3c59a902a00))
* type bot and webhook bootstrap stages ([6827f7b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6827f7bf76c1dcb94329ac39cf7af1e2aa1b7bb2))
* type core bootstrap sync and migration stages ([0498b5a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0498b5abb552808825bda07555c8d98a02676cac))
* type core runtime startup task contracts ([5dad0d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5dad0d6882795eca689e145734b84e92111d441d))
* type integration bootstrap startup stages ([30ef194](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/30ef1945dec2997c9a59a7b814ca6a8181fad386))
* type payment runtime bootstrap interfaces ([8f748bb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8f748bbf60e96249796801d0786aa3d503cfa563))
* type remaining bootstrap utility stages ([d10758a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d10758a313e46dbbc605cc59c04e773982110669))
* type runtime task startup stages ([7049e18](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7049e18c4bf9b86e768010b06b98c12d283950d9))
* type runtime watchdog loop interfaces ([ae2fdab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ae2fdab62bd514de6847bf0332b5446a2f1adc2e))
* type startup summary and finalize stages ([68cd40c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/68cd40c8f166628b25edeffc39ede9778e2c4111))
* type telegram notifier in bootstrap pipeline ([f206570](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f2065708fc8fc8eae5a757bf302d71f45ed52c9a))
* unify alembic command executor path ([ba974f6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ba974f635afaefc0bce921e9765e215f682211e1))
* unify payment CRUD compatibility wrappers ([0d944e9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0d944e9222ca3a7311c608f54f17f162fa4b1e8e))
* unify runtime startup stage invocation ([5159106](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5159106d03c1eb05fc1b08c8df14a64b05a0c17d))
* unify runtime task shutdown handling ([8520d14](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8520d14a011d9ced7c8950480ce7389201d441df))
* unify web shutdown guarded calls ([a00ebbd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a00ebbd4c8921065bf9f8a238276653dce4878fb))
* use running loop in broadcast timing paths ([9f7e6ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f7e6ee0704297904e73622fe685a5e7159a64ec))

## [3.19.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.18.0...v3.19.0) (2026-02-20)


### New Features

* **cabinet:** add admin menu-layout endpoints ([4e8a3ce](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4e8a3ce020d27b50d710e2581404538867bfda8a))


### Bug Fixes

* **menu:** enable custom buttons in cabinet mode ([3e08e6a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3e08e6ad65379a8190efcfb74b3772780f0f7160))
* skip blocked users in trial notifications and broadcasts without DB status change ([493f315](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/493f315a65610826a04e04c3d2065e0b395426ed))

## [3.18.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.17.1...v3.18.0) (2026-02-18)


### New Features

* add campaign_id to ReferralEarning for campaign attribution ([0c07812](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c07812ecc9502f54a7745a77b086fc52bdc0e34))
* enforce 1-to-1 partner-campaign binding with partner info in campaigns ([366df18](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/366df18c547047a7c69192c768970ebc6ee426fc))
* expose traffic_reset_mode in subscription response ([59383bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/59383bdbd8c72428d151cb24d132452414b14fa3))
* expose traffic_reset_mode in tariff API response ([5d4a94b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5d4a94b8cea8f16f0b4c31e24a4695bee4c67af7))


### Bug Fixes

* 3 user deletion bugs — type cast, inner savepoint, lazy load ([af31c55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/af31c551d2f23ef01425bdb2db8f255dbc3047e2))
* add blocked_count column migration to universal_migration.py ([b4b10c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b4b10c998cadbb879540e56dbd0e362b5497ee57))
* add migration for partner system tables and columns ([4645be5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4645be53cbb3799aa6b2b6a623af30460357a554))
* add migration for partner system tables and columns ([79ea398](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79ea398d1db436a7812a799bf01b2c1c3b1b73be))
* add missing payment providers to payment_utils and fix {total_amount} formatting ([bdb6161](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bdb61613de378efab4de6de98fde2de3b554c548))
* add selectinload for subscription in campaign user list ([eb9dba3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eb9dba3f4728b478f2206ff992700a9677f879c7))
* **async:** offload blocking Path operations to threads ([9d298fa](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d298fabad791e2d2ba48950f44e8e1f2e90cca5))
* auth middleware catches all commit errors, not just connection errors ([6409b0c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6409b0c023cd7957c43d5c1c3d83e671ccaf959c))
* auto-convert naive datetimes to UTC-aware on model load ([f7d33a7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f7d33a7d2b31145a839ee54676816aa657ac90da))
* connected_squads stores UUIDs, not int IDs — use get_server_ids_by_uuids ([d7039d7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d7039d75a47fbf67436a9d39f2cd9f65f2646544))
* correct subscription_service import in broadcast cleanup ([6c4e035](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c4e035146934dffb576477cc75f7365b2f27b99))
* deadlock on user deletion + robust migration 0002 ([b7b83ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7b83abb723913b3167e7462ff592a374c3f421b))
* eliminate deadlock by matching lock order with webhook ([d651a6c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d651a6c02f501b7a0ded570f2db6addcc16173a9))
* extend naive datetime guard to all model properties ([bd11801](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bd11801467e917d76005d1a782c71f5ae4ffee6e))
* handle naive datetime in raw SQL row comparison (payment/common) ([38f3a9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/38f3a9a16a24e85adf473f2150aad31574a87060))
* handle naive datetimes in Subscription properties ([e512e5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e512e5fe6e9009992b5bc8b9be7f53e0612f234a))
* make migration 0002 robust with table existence checks ([f076269](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f076269c323726c683a38db092d907591a26e647))
* prevent fileConfig from destroying structlog handlers ([e78b104](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e78b1040a50ac14759bceab396d0c3e34dd79cdd))
* return zeroed stats dict when withdrawal is disabled ([7883efc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7883efc3d6e6d8bedf8e4b7d72634cbab6e2f3d7))
* use AwareDateTime TypeDecorator for all datetime columns ([a7f3d65](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a7f3d652c51ecd653900a530b7d38feaf603ecf1))
* wrap user deletion steps in savepoints to prevent transaction cascade abort ([a38dfcb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a38dfcb75a47a185d979a8202f637d8b79812e67))


### Refactoring

* replace universal_migration.py with Alembic ([b6c7f91](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6c7f91a7c79d108820c9f89c9070fde4843316c))
* replace universal_migration.py with Alembic ([784616b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/784616b349ef12b35ee021dd7a7b2a2ef9fc57f6))

## [3.17.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.17.0...v3.17.1) (2026-02-18)


### Bug Fixes

* **account-linking:** humanize manual merge ticket messages in russian ([90ca1ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/90ca1ab380e643310833afe4877cc9daa9f461ce))
* **account-linking:** humanize manual merge ticket messages in russian ([eddc04b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eddc04b05aa708e6b9b3bda9196d003a65f9a41d))

## [3.17.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.16.1...v3.17.0) (2026-02-18)


### New Features

* **account-linking:** expose telegram relink cooldown metadata ([113148a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/113148a10675240423c2e0566dd649e1785cf2f2))
* **account-linking:** expose telegram relink cooldown metadata ([ec50d64](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec50d6450a31971988882fd76b3de08537ca4a50))

## [3.16.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.16.0...v3.16.1) (2026-02-17)


### Bug Fixes

* resolve ruff lint violations and align lint config ([c7b456e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c7b456efbba9498400fb0efeb401299787656fec))

## [3.16.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.15.1...v3.16.0) (2026-02-17)


### New Features

* **account-linking:** add coded errors and manual merge ticket flow ([75798ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/75798aef470ac69bb1d9fa67f9dac44b60e23cae))
* **account-linking:** add secure link-code flow for auth providers ([2e7a601](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2e7a60142c76bf10ef3422becbf33cc7a4aab06c))
* **account-linking:** localize manual merge tickets and enforce telegram relink guard ([bfa2c31](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bfa2c31aa9faa2f49c7e3f6a41d2c166d87ee5c2))
* add 'default' (no color) option for button styles ([10538e7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/10538e735149bf3f3f2029ff44b94d11d48c478e))
* add admin device management endpoints ([c57de10](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c57de1081a9e905ba191f64c37221c36713c82a6))
* add admin traffic packages and device limit management ([2f90f91](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2f90f9134df58b8c0a329c20060efcf07d5d92f9))
* add admin traffic usage API ([aa1cd38](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa1cd3829c5c3671e220d49dd7ec2d83563e2cf9))
* add admin traffic usage API with per-node statistics ([6c2c25d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c2c25d2ccb27446c822e4ed94d9351bfeaf4549))
* add admin updates endpoint for bot and cabinet releases ([11b8ab1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11b8ab1959e83fafe405be0b76dfa3dd1580a68b))
* add all remaining RemnaWave webhook events (node, service, crm, device) ([1e37fd9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e37fd9dd271814e644af591343cada6ab12d612))
* add button style and emoji support for cabinet mode (Bot API 9.4) ([bf2b2f1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf2b2f1c5650e527fcac0fb3e72b4e6e19bef406))
* add cabinet admin API for pinned messages management ([1a476c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1a476c49c19d1ec2ab2cda1c2ffb5fd242288bb6))
* add close button to all webhook notifications ([d9de15a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d9de15a5a06aec3901415bdfd25b55d2ca01d28c))
* add endpoint for updating user referral commission percent ([da6f746](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/da6f746b093be8cdbf4e2889c50b35087fbc90de))
* add enrichment data to CSV export ([f2dbab6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f2dbab617155cdc41573d885f0e55222e5b9825b))
* add lite mode functionality with endpoints for retrieval and update ([7b0403a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7b0403a307702c24efefc5c14af8cb2fb7525671))
* add LOG_COLORS env setting to toggle console ANSI colors ([27309f5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27309f53d9fa0ba9a2ca07a65feed96bf38f470c))
* add MULENPAY_WEBSITE_URL setting for post-payment redirect ([fe5f5de](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fe5f5ded965e36300e1c73f25f16de22f84651ad))
* add node/status filters and custom date range to traffic page ([ad260d9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad260d9fe0b232c9d65176502476212902909660))
* add node/status filters, custom date range, connected devices to traffic page ([9ea533a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ea533a864e345647754f316bd27971fba1420af))
* add node/status filters, date range, devices to traffic page ([ad6522f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad6522f547e68ef5965e70d395ca381b0a032093))
* add OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([97be4af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97be4afbffd809fe2786a6d248fc4d3f770cb8cf))
* add panel info, node usage endpoints and campaign to user detail ([287a43b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/287a43ba6527ff3464a527821d746a68e5371bbe))
* add panel info, node usage endpoints and campaign to user detail ([0703212](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/070321230bcb868e4bc7a39c287ed3431a4aef4a))
* add per-button enable/disable toggle and custom labels per locale ([68773b7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/68773b7e77aa344d18b0f304fa561c91d7631c05))
* add per-section button style and emoji customization via admin API ([a968791](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a9687912dfe756e7d772d96cc253f78f2e97185c))
* add Persian (fa) locale with complete translations ([29a3b39](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/29a3b395b6e67e4ce2437b75120b78c76b69ff4f))
* add RemnaWave incoming webhooks for real-time subscription events ([6d67cad](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6d67cad3e7aa07b8490d88b73c38c4aca6b9e315))
* add risk columns to traffic CSV export ([7c1a142](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7c1a1426537e43d14eff0a1c3faeca484611b58b))
* add server-side sorting for enrichment columns ([15c7cc2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/15c7cc2a58e1f1935d10712a981466629db251d1))
* add startup warnings for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE and MINIAPP_CUSTOM_URL ([476b89f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/476b89fe8e613c505acfc58a9554d31ccf92718a))
* add system info endpoint for admin dashboard ([02c30f8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02c30f8e7eb6ba90ed8983cfd82199a22b473bbf))
* add tariff filter, fix traffic data aggregation ([fa01819](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fa01819674b2d2abb0d05b470559b09eb43abef8))
* add tariff reorder API endpoint ([4c2e11e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4c2e11e64bed41592f5a12061dcca74ce43e0806))
* add traffic usage enrichment endpoint with devices, spending, dates, last node ([5cf3f2f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5cf3f2f76eb2cd93282f845ea0850f6707bfcc09))
* add TRIAL_DISABLED_FOR setting to disable trial by user type ([c4794db](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c4794db1dd78f7c48b5da896bdb2f000e493e079))
* add user_id filter to admin tickets endpoint ([8886d0d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8886d0dea20aa5a31c6b6f0c3391b3c012b4b34d))
* add user_id filter to admin tickets endpoint ([d3819c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d3819c492f88794e4466c2da986fd3a928d7f3df))
* add web admin button for admins in cabinet mode ([9ac6da4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ac6da490dffa03ce823009c6b4e5014b7d2bdfb))
* add web campaign links with bonus processing in auth flow ([d955279](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d9552799c17a76e2cc2118699528c5b591bd97fb))
* admin panel enhancements & bug fixes ([e6ebf81](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e6ebf81752499df8eb0a710072785e3d603dba33))
* allow tariff deletion with active subscriptions ([ebd6bee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ebd6bee05ed7d9187de9394c64dfd745bb06b65a))
* **auth:** add manual merge moderation and secure telegram-otp unlink flow ([ab281f4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ab281f40aa8e3dffdfb123c24f046ce10a71a8f3))
* block registration with disposable email addresses ([9ca24ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ca24efe434278925c0c1f8d2f2d644a67985c89))
* block registration with disposable email addresses ([116c845](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/116c8453bb371b5eacf5c9d07f497eb449a355cc))
* **ci:** add release-please and release workflows ([488d5c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/488d5c99f7bd6bd1927e2125a824d43376cf3403))
* **ci:** add release-please and release workflows ([9151882](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9151882245a325761d75eab3a58d0f677219c31b))
* colored console logs via structlog + rich + FORCE_COLOR ([bf64611](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf646112df02aa7aa7918d0513cb6968ceb7f378))
* disable trial by user type (email/telegram/all) ([4e7438b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4e7438b9f9c01e30c48fcf2bbe191e9b11598185))
* handle errors.bandwidth_usage_threshold_reached_max_notifications webhook ([8e85e24](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8e85e244cb786fb4c06162f2b98d01202e893315))
* handle service.subpage_config_changed webhook event ([43a326a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43a326a98ccc3351de04d9b2d660d3e7e0cb0efc))
* **localization:** add Persian (fa) locale support and wire it across app flows ([cc54a7a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cc54a7ad2fb98fe6e662e1923027f4989ae72868))
* migrate OAuth state storage from in-memory to Redis ([e9b98b8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e9b98b837a8552360ef4c41f6cd7a5779aa8b0a7))
* node/status filters + custom date range for traffic page ([a161e2f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a161e2f904732b459fef98a67abfaae1214ecfd4))
* **notifications:** redesign version update notification ([02eca28](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02eca28bc0f9d31495d7bbe5deb380d13e859c3f))
* **notifications:** redesign version update notification ([3f7ca7b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3f7ca7be3ade6892e453f86ac0c62e61ac61a11c))
* OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([3cbb9ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3cbb9ef024695352959ef9a82bf8b81f0ba1d940))
* pass platform-level fields from RemnaWave config to frontend ([095bc00](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/095bc00b33d7082558a8b7252906db2850dce9da))
* rename MAIN_MENU_MODE=text to cabinet with deep-linking to frontend sections ([ad87c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad87c5fb5e1a4dd0ef7691f12764d3df1530f643))
* return 30-day daily breakdown for node usage ([7102c50](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7102c50f52d583add863331e96f3a9de189f581a))
* return 30-day daily breakdown for node usage ([e4c65ca](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e4c65ca220994cf08ed3510f51d9e2808bb2d154))
* serve original RemnaWave config from app-config endpoint ([43762ce](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43762ce8f4fa7142a1ca62a92b97a027dab2564d))
* show all active webhook endpoints in startup log ([9d71005](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d710050ad40ba76a14aa6ace8e8a47f25cdde94))
* tariff filter + fix traffic data aggregation ([1021c2c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1021c2cdcd07cf2194e59af7b59491108339e61f))
* tariff reorder API endpoint ([085a617](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/085a61721a8175b3f4fd744614c446d73346f2b7))
* traffic filters, date range & risk columns in CSV export ([4c40b5b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4c40b5b370616a9ab40cbf0cccdbc0ac4a3f8278))
* unified notification delivery for webhook events (email + WS support) ([26637f0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/26637f0ae5c7264c0430487d942744fd034e78e8))
* webhook protection — prevent sync/monitoring from overwriting webhook data ([184c52d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/184c52d4ea3ce02d40cf8a5ab42be855c7c7ae23))


### Bug Fixes

* **account-linking:** allow auto-merge when source has trial only ([c3713f7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c3713f7e628e57559890dde10de86368bc560505))
* **account-linking:** allow merge with trial remna and transfer balance ([5cc3ec6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5cc3ec6a7a0febe0cba9a6d00fe939ef22ba6381))
* **account-linking:** allow unlink of current auth provider when other identities exist ([afdc2f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/afdc2f2956874c23ce5a092266c21282594d28ae))
* **account-linking:** apply telegram relink cooldown to resulting primary account ([9facc81](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9facc810528a5fdb3995bb0cce7404ecf15f585d))
* **account-linking:** auto-select primary account by data presence ([5815a7d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5815a7d0ef44a9f2d6533b1ff3c0fcc4b1e8daf7))
* **account-linking:** handle external identity unique conflicts ([a43c9a9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a43c9a94ec0de3113f407986242ed1fb9d7c4c8c))
* **account-linking:** make manual merge resolution messages human-readable ([615d7c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/615d7c411675543bccfc4a30275f722e1a14092b))
* add /start burst rate-limit to prevent spam abuse ([61a9722](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/61a97220d30031816ab23e33a46717e4895c0758))
* add action buttons to webhook notifications and fix empty device names ([7091eb9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7091eb9c148aaf913c4699fc86fef5b548002668))
* add debug logging for bulk device response structure ([46da31d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46da31d89c55c225dec9136d225f2db967cf8961))
* add email field to traffic table for OAuth/email users ([94fcf20](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/94fcf20d17c54efd67fa7bd47eff1afdd1507e08))
* add email/UUID fallback for OAuth user panel sync ([165965d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/165965d8ea60a002c061fd75f88b759f2da66d7d))
* add enrichment device mapping debug logs ([5be82f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5be82f2d78aed9b54d74e86f261baa5655e5dcd9))
* add missing placeholders to Arabic SUBSCRIPTION_INFO template ([fe54640](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fe546408857128649930de9473c7cde1f7cc450a))
* add naive datetime guards to fromisoformat() in Redis cache readers ([1b3e6f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1b3e6f2f11c20aa240da1beb11dd7dfb20dbe6e8))
* add naive datetime guards to fromisoformat() in Redis cache readers ([6fa4948](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6fa49485d9f1cd678cb5f9fa7d0375fd47643239))
* add naive datetime guards to parsers and fix test datetime literals ([0946090](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/094609005af7358bf5d34d252fc66685bd25751c))
* add passive_deletes to Subscription relationships to prevent NOT NULL violation on cascade delete ([bfd66c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bfd66c42c1fba3763f41d641cea1bd101ec8c10c))
* add promo code anti-abuse protections ([97ec39a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97ec39aa803f0e3f03fdcd482df0cbcb86fd1efd))
* add refresh before assigning promo_groups to avoid async lazy lo… ([733be09](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/733be0965806607cef8beb30685052af22a13ab4))
* add refresh before assigning promo_groups to avoid async lazy load error ([5e75210](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5e75210c8b3da1a738c94edf3dd02a18bbff3bb6))
* add startup warning for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE in guide mode ([1d43ae5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1d43ae5e25ffcf0e4fe6fec13319d393717e1e50))
* address remaining abs() issues from review ([ff21b27](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff21b27b98bb5a7517e06057eb319c9f3ebb74c7))
* address review issues in backup, updates, and webhook handlers ([2094886](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/20948869902dc570681b05709ac8d51996330a6e))
* allow email change for unverified emails ([93bb8e0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/93bb8e0eb492ca59e29da86594e84e9c486fea65))
* allow non-HTTP deep links in crypto link webhook updates ([f779225](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f77922522a85b3017be44b5fc71da9c95ec16379))
* allow purchase when recalculated price is lower than cached ([19dabf3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/19dabf38512ae0c2121108d0b92fc8f384292484))
* AttributeError in withdrawal admin notification (send_to_admins → send_admin_notification) ([c75ec0b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c75ec0b22a3f674d3e1a24b9d546eca1998701b3))
* **auth:** add unlink otp anti-spam limits ([5a14d7a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a14d7a901ff9e4afb0c6082e6725eb0d7a6a78e))
* **autopay:** add 6h cooldown for insufficient balance notifications ([f7abe03](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f7abe03dba085b07fc1dc0fc0f21613e6a6219eb))
* **autopay:** add 6h cooldown for insufficient balance notifications ([992a5cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/992a5cb97f5517b52bd386907a2cbc2162182c44))
* **autopay:** exclude daily subscriptions from global autopay ([3d94e63](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3d94e63c3ca4688d5f0b513e6b678afdd3798eea))
* **autopay:** exclude daily subscriptions from global autopay ([b9352a5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b9352a5bd53ec82114abd46156bacc0e496dcfe1))
* **broadcast:** resolve SQLAlchemy connection closed errors ([94a00ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/94a00ab2694d2b13c93c73a4defb2c2019225093))
* **broadcast:** resolve SQLAlchemy connection closed errors during long broadcasts ([b8682ad](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b8682adbbfa1674f03ea8699de4b3bd125092a9b))
* **broadcast:** stabilize mass broadcast for 100k+ users ([7956951](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79569510d29494c0be46a8f39bc4a01e30873f21))
* **broadcast:** stabilize mass broadcast for 100k+ users ([13ebfdb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/13ebfdb5c45f2d358b2552bfcc2e3b907ec7d567))
* build composite device name from platform + hwid short suffix ([17ce640](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17ce64037f198837c8f2aa7bf863871f60bdf547))
* **cabinet:** apply promo group discounts to addons and tariff switch ([e8a413c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e8a413c3c3177d8ce4931d2f82c17dce70e9aaad))
* **cabinet:** apply promo group discounts to device/traffic purchase and tariff switch ([aa1d328](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa1d3289e1bb2195a11c333867ac131c5460f0cc))
* change CryptoBot URL priority to bot_invoice_url for Telegram opening ([3193ffb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3193ffbd1bee07cb79824d87cb0f77b473b22989))
* clean stale squad UUIDs from tariffs during server sync ([fcaa9df](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fcaa9dfb27350ceda3765c6980ad67f671477caf))
* clear subscription data when user deleted from Remnawave panel ([b0fd38d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b0fd38d60c22247a0086c570665b92c73a060f2f))
* close unclosed HTML tags in version notification ([0b61c7f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b61c7fe482e7bbfbb3421307a96d54addfd91ee))
* close unclosed HTML tags when truncating version notification ([b674550](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6745508da861af9b2ff05d89b4ac9a3933da510))
* complete datetime.utcnow() → datetime.now(UTC) migration ([eb18994](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eb18994b7d34d777ca39d3278d509e41359e2a85))
* correct response parsing for non-legacy node-users endpoint ([a076dfb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a076dfb5503a349450b5aa8aac3c6f40070b715d))
* correct response parsing for non-legacy node-users endpoint ([91ac90c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/91ac90c2aecfb990679b3d0c835314dde448886a))
* daily tariff subscriptions stuck in expired/disabled with no resume path ([80914c1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/80914c1af739aa0ee1ea75b0e5871bf391b9020d))
* delete subscription_servers before subscription to prevent FK violation ([7d9ced8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7d9ced8f4f71b43ed4ac798e6ff904a086e1ac4a))
* don't delete Heleket invoice message on status check ([9943253](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/994325360ca7665800177bfad8f831154f4d733f))
* downgrade Telegram timeout errors to warning in monitoring service ([e43a8d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e43a8d6ce4c40a7212bf90644f82da109717bdcb))
* downgrade transient API errors (502/503/504) to warning level ([ec8eaf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec8eaf52bfdc2bde612e4fc0324575ba7dc6b2e1))
* enforce blacklist via middleware ([561708b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/561708b7772ec5b84d6ee049aeba26dc70675583))
* enforce blacklist via middleware instead of per-handler checks ([966a599](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/966a599c2c778dce9eea3c61adf6067fb33119f6))
* exclude signature field from Telegram initData HMAC validation ([5b64046](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5b6404613772610c595e55bde1249cdf6ec3269d))
* expand backup coverage to all 68 models and harden restore ([02e40bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02e40bd6f7ef8e653cae53ccd127f2f79009e0d4))
* extract device name from nested hwidUserDevice object ([79793c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79793c47bbbdae8b0f285448d5f70e90c9d4f4b0))
* filter out traffic packages with zero price from purchase options ([64a684c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/64a684cd2ff51e663a1f70e61c07ca6b4f6bfc91))
* flood control handling in pinned messages and XSS hardening in HTML sanitizer ([454b831](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/454b83138e4db8dc4f07171ee6fe262d2cd6d311))
* force basicConfig to replace pre-existing handlers ([7eb8d4e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7eb8d4e153bab640a5829f75bfa6f70df5763284))
* handle FK violation in create_yookassa_payment when user is deleted ([55d281b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/55d281b0e37a6e8977ceff792cccb8669560945b))
* handle mixed types in traffic sort ([eeed2d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eeed2d6369b07860505c59bcff391e7b17e0ffb7))
* handle mixed types in traffic sort for string fields ([a194be0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a194be0843856b3376167d9ba8a8ef737280998c))
* handle nullable traffic_limit_gb and end_date in subscription model ([e94b93d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e94b93d0c10b4e61d7750ca47e1b2f888f5873ed))
* handle photo message in ticket creation flow ([e182280](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1822800aba3ea5eee721846b1e0d8df0a9398d1))
* handle StaleDataError in webhook user.deleted server counter decrement ([c30c2fe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c30c2feee1db03f0a359b291117da88002dd0fe0))
* handle StaleDataError in webhook when user already deleted ([d58a80f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d58a80f3eaa64a6fc899e10b3b14584fb7fc18a9))
* handle tariff_extend callback without period (back button crash) ([ba0a5e9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ba0a5e9abd9bd582968d69a5c6e57f336094c782))
* handle TelegramBadRequest in ticket edit_message_text calls ([8e61fe4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8e61fe47746da2ac09c3ea8c4dbfc6be198e49e3))
* handle time/date types in backup JSON serialization ([27365b3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27365b3c7518c09229afcd928f505d0f3f66213f))
* handle unique constraint conflicts during backup restore without clear_existing ([5893874](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/589387477624691e0026086800428e7e52e06128))
* harden backup create/restore against serialization and constraint errors ([fc42916](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fc42916b10bb698895eb75c0e2568747647555d3))
* HTML parse fallback, email change race condition, username length limit ([d05ff67](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d05ff678abfacaa7e55ad3e55f226d706d32a7b7))
* ignore 'message is not modified' on privacy policy decline ([be1da97](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/be1da976e14a35e6cca01a7fca7529c55c1a208b))
* improve button URL resolution and pass uiConfig to frontend ([0ed98c3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0ed98c39b6c95911a38a26a32d0ffbcf9cfd7c80))
* include additional devices in tariff renewal price and display ([17e9259](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17e9259eb1d41dbf1d313b6a7d500f6458359393))
* increase OAuth HTTP timeout to 30s ([333a3c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/333a3c590120a64f6b2963efab1edd861274840c))
* limit Rich traceback output to prevent console flood ([11ef714](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11ef714e0dde25a08711c0daeee943b6e71e20b7))
* move /settings routes before /{ticket_id} to fix route matching ([000d670](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/000d670869bc7eb0eb6551e1d9eabbe05cd34ea2))
* move /settings routes before /{ticket_id} to fix route matching ([0c9b69d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c9b69deb0686c8e078eaf627693b84b03ffdd3c))
* NameError in set_user_devices_button — undefined action_text ([1b8ef69](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1b8ef69a1bbb7d8d86827cf7aaa4f05cbf480d75))
* normalize transaction amount signs across all aggregations ([4247981](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4247981c98111af388c98628c1e61f0517c57417))
* nullify payment FK references before deleting transactions in user restoration ([0b86f37](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b86f379b4e55e499ca3d189137e2aed865774b5))
* **oauth:** add yandex retry and fallback endpoints ([4633351](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46333517c8ba69de67b1e0be2e73517e50a3e94c))
* **oauth:** backfill missing profile fields on login ([1e545d7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e545d71394fc3f25b4f3b0b92c06f112f48195c))
* **oauth:** fill vk profile fallbacks for empty userinfo ([410870c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/410870cb9798983e8b5801bf4147973390fb4baa))
* **oauth:** migrate vk login to vk id pkce flow ([15a22bf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/15a22bfb1a3a4ba6573a4865086e4b54064ed5e8))
* **oauth:** use yandex.ru authorize endpoint ([ea2fdda](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ea2fddaadbf0ad01b5ebe6821651a74be6960518))
* paginate bulk device endpoint to fetch all HWID devices ([4648a82](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4648a82da959410603c92055bcde7f96131e0c29))
* parse bandwidth stats series format for node usage ([557dbf3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/557dbf3ebe777d2137e0e28303dc2a803b15c1c6))
* parse bandwidth stats series format for node usage ([462f7a9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/462f7a99b9d5c0b7436dbc3d6ab5db6c6cfa3118))
* pass tariff object instead of tariff_id to set_tariff_promo_groups ([1ffb8a5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1ffb8a5b85455396006e1fcddd48f4c9a2ca2700))
* payment race conditions, balance atomicity, renewal rollback safety ([c5124b9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c5124b97b63eda59b52d2cbf9e2dcdaa6141ed6e))
* pre-validate CABINET_BUTTON_STYLE to prevent invalid values from suppressing per-section defaults ([46c1a69](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46c1a69456036cb1be784b8d952f27110e9124eb))
* preserve payment initiation time in transaction created_at ([90d9df8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/90d9df8f0e949913f09c4ebed8fe5280453ab3ab))
* preserve purchased traffic when extending same tariff ([b167ed3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b167ed3dd1c6e6239db2bdbb8424bcb1fb7715d9))
* prevent cascading greenlet errors after sync rollback ([a1ffd5b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a1ffd5bda6b63145104ce750835d8e6492d781dc))
* prevent negative amounts in spent display and balance history ([c30972f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c30972f6a7911a89a6c3f2080019ff465d11b597))
* prevent sync from overwriting end_date for non-ACTIVE panel users ([49871f8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/49871f82f37d84979ea9ec91055e3f046d5854be))
* promo code max_uses=0 conversion and trial UX after promo activation ([1cae713](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1cae7130bc87493ab8c7691b3c22ead8189dab55))
* protect server counter callers and fix tariff change detection ([bee4aa4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bee4aa42842b8b6611c7c268bcfced408a227bc0))
* query per-node legacy endpoint for user traffic breakdown ([b94e3ed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b94e3edf80e747077992c03882119c7559ad1c31))
* query per-node legacy endpoint for user traffic breakdown ([51ca3e4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/51ca3e42b75c1870c76a1b25f667629855cfe886))
* read bot version from pyproject.toml when VERSION env is not set ([9828ff0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9828ff0845ec1d199a6fa63fe490ad3570cf9c8f))
* reduce node usage to 2 API calls to avoid 429 rate limit ([c68c4e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c68c4e59846abba9c7c78ae91ec18e2e0e329e3c))
* reduce node usage to 2 API calls to avoid 429 rate limit ([f00a051](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f00a051bb323e5ba94a3c38939870986726ed58e))
* release-please config — remove blocked workflow files ([d88ca98](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d88ca980ec67e303e37f0094a2912471929b4cef))
* remove DisplayNameRestrictionMiddleware ([640da34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/640da3473662cfdcceaa4346729467600ac3b14f))
* remove dots from Remnawave username sanitization ([d6fa86b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d6fa86b870eccbf22327cd205539dd2084f0014e))
* remove local UTC re-imports shadowing module-level import in purchase.py ([e68760c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e68760cc668016209f4f19a2e08af8680343d6ed))
* remove redundant trial inactivity monitoring checks ([d712ab8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d712ab830166cab61ce38dd32498a8a9e3e602b0))
* remove unused PaymentService from MonitoringService init ([491a7e1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/491a7e1c425a355e55b3020e2bcc7b96047bdf5e))
* remove workflow files and pyproject.toml from release-please extra-files ([5070bb3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5070bb34e8a09b2641783f5e818bb624469ad610))
* replace deprecated Query(regex=) with pattern= ([871ceb8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/871ceb866ccf1f3a770c7ef33406e1a43d0a7ff7))
* resolve 429 rate limiting on traffic page ([b12544d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b12544d3ea8f4bbd2d8c941f83ee3ac412157adb))
* resolve 429 rate limiting on traffic page ([924d6bc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/924d6bc09c815c1d188ea1d0e7974f7e803c1d3f))
* resolve deadlock on server_squads counter updates and add webhook notification toggles ([57dc1ff](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/57dc1ff47f2f6183351db7594544a07ca6f27250))
* resolve exc_info for admin notifications, clean log formatting ([11f8af0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11f8af003fc60384abafa2b670b89d6ad3ac57a4))
* resolve HWID reset and webhook FK violation ([5f3e426](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5f3e426750c2adcb097b92f1a9e7725b1c5c5eba))
* resolve HWID reset context manager bug and webhook FK violation ([a9eee19](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a9eee19c95efdc38ecf5fa28f7402a2bbba7dd07))
* resolve merge conflict in release-please config ([0ef4f55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0ef4f55304751571754f2027105af3e507f75dfd))
* resolve MissingGreenlet error when accessing subscription.tariff ([a93a32f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a93a32f3a7d1b259a2e24954ae5d2b7c966c5639))
* resolve multiple production errors and performance issues ([071c23d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/071c23dd5297c20527442cb5d348d498ebf20af4))
* restore unquote for user data parsing in telegram auth ([c2cabbe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c2cabbee097a41a95d16c34d43ab7e70d076c4dc))
* revert device pagination, add raw user data field discovery ([8f7fa76](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8f7fa76e6ab34a3ad2f61f4e1f06026fd3fbf4e3))
* safe HTML preview truncation and lazy-load subscription fallback ([40d8a6d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/40d8a6dc8baf3f0f7c30b0883898b4655a907eb5))
* security and architecture fixes for webhook handlers ([dc1e96b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc1e96bbe9b4496e91e9dea591c7fc0ef4cc245b))
* skip users with active subscriptions in admin inactive cleanup ([e79f598](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e79f598d17ffa76372e6f88d2a498accf8175c76))
* stop CryptoBot webhook retry loop and save cabinet payments to DB ([2cb6d73](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2cb6d731e96cbfc305b098d8424b84bfd6826fb4))
* suppress 'message is not modified' error in updates panel ([3a680b4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3a680b41b0124848572809d187cab720e1db8506))
* suppress bot-blocked-by-user error in AuthMiddleware ([fda9f3b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fda9f3beecbfcca4d7abc16cf661d5ad5e3b5141))
* suppress expired callback query error in AuthMiddleware ([2de4384](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2de438426a647e2bcae9b4d99eef4093ff8b5429))
* suppress startup log noise (~350 lines → ~30) ([8a6650e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8a6650e57cd8ea396d9b057a7753469947f38d29))
* sync subscription status from panel in user.modified webhook ([5156d63](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5156d635f0b5bc0493e8f18ce9710cca6ff4ffc8))
* sync support mode from cabinet admin to SupportSettingsService ([516be6e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/516be6e600a08ad700d83b793dc64b2ca07bdf44))
* sync SUPPORT_SYSTEM_MODE between SystemSettings and SupportSettings ([0807a9f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0807a9ff19d1eb4f1204f7cbeb1da1c1cfefe83a))
* ticket creation crash and webhook PendingRollbackError ([760c833](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/760c833b7402541d3c7cf2ed7fc0418119e75042))
* traceback in Telegram notifications + reduce log padding ([909a403](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/909a4039c43b910761bd05c36e79c8e6773199db))
* UnboundLocalError for get_logo_media in required_sub_channel_check ([d3c14ac](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d3c14ac30363839d1340129f279a7a7b4b021ed1))
* use accessible nodes API and fix date format for node usage ([943e9a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/943e9a86aaa449cd3154b0919cfdc52d2a35b509))
* use accessible nodes API and fix date format for node usage ([c4da591](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c4da59173155e2eeb69eca21416f816fcbd1fa9c))
* use actual DB columns for subscription fallback query ([f0e7f8e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f0e7f8e3bec27d97a3f22445948b8dde37a92438))
* use bulk device endpoint instead of per-user calls ([5f219c3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5f219c33e6d49b0e3e4405a57f8344a4237f1002))
* use callback fallback when MINIAPP_CUSTOM_URL is not set ([eaf3a07](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eaf3a07579729031030308d77f61a5227b796c02))
* use correct pagination params (start/size) for bulk HWID devices ([17af51c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17af51ce0bdfa45197384988d56960a1918ab709))
* use event field directly as event_name (already includes scope prefix) ([9aa22af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9aa22af3390a249d1b500d75a7d7189daaed265e))
* use flush instead of commit in server counter functions ([6cec024](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6cec024e46ef9177cb59aa81590953c9a75d81bb))
* use legacy per-node endpoint for traffic aggregation ([cc1c8ba](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cc1c8bacb42a9089021b7ae0fecd1f2717953efb))
* use legacy per-node endpoint with correct response format ([b707b79](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b707b7995b90c6465910a35e9a4403e1408c6568))
* use PaymentService for cabinet YooKassa payments ([61bb8fc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/61bb8fcafd94509568f134ccdba7769b66cc7d5d))
* use PaymentService for cabinet YooKassa payments to save local DB record ([ff5bba3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff5bba3fc5d1e1b08d008b64215e487a9eb70960))
* use per-user panel endpoints for reliable device counts and last node data ([9d39901](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d39901f78ece55c740a5df2603601e5d0b1caca))
* use selection.period.days instead of selection.period_days ([4541016](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/45410168afe683675003a1c41c17074a54ce04f1))
* use sync context manager for structlog bound_contextvars ([25e8c9f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/25e8c9f8fc4d2c66d5a1407d3de5c7402dc596da))
* use traffic topup config and add WATA 429 retry ([b5998ea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b5998ea9d22644ed2914b0e829b3a76a32a69ddf))
* webhook notification 'My Subscription' button uses unregistered callback_data ([1e2a7e3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e2a7e3096af11540184d60885b8c08d73506c4a))
* webhook:close button not working due to channel check timeout ([019fbc1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/019fbc12b6cf61d374bbed4bce3823afc60445c9))


### Performance

* cache logo file_id to avoid re-uploading on every message ([142ff14](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/142ff14a502e629446be7d67fab880d12bee149d))


### Refactoring

* add strict typing to OAuth providers, replace urlencode with httpx params ([0de6418](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0de6418bca39fb1b72c49d7c89d1a169722ec9e8))
* complete structlog migration with contextvars, kwargs, and logging hardening ([1f0fef1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f0fef114bd979b2b0d2bd38dde6ce05e7bba07b))
* fix transaction boundaries, extract _finalize_oauth_login, replace deprecated datetime.utcnow ([41633af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/41633af7631cce084f9ff6e7ceb27b27ed340d95))
* improve log formatting — logger name prefix and table alignment ([f637204](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f63720467a935bdaaa58bb34d588d65e46698f26))
* remove "both" mode from BOT_RUN_MODE, keep only polling and webhook ([efa3a5d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/efa3a5d4579f24dabeeba01a4f2e981144dd6022))
* remove duplicated helpers, import from auth.py ([ccd9ab0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ccd9ab02c5b7add1440efc6f1aafc93bb668e57a))
* remove Flask, use FastAPI exclusively for all webhooks ([119f463](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/119f463c36a95685c3bc6cdf704e746b0ba20d56))
* remove modem functionality from classic subscriptions ([ee2e79d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ee2e79db3114fe7a9852d2cd33c4b4fbbde311ea))
* remove smart auto-activation & activation prompt, fix production bugs ([a3903a2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a3903a252efdd0db4b42ca3fd6771f1627050a7f))
* replace dataclass with BaseModel for OAuthUserInfo ([d0a9cfe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d0a9cfe6a9611749ee215377ce632da64d393216))

## [3.15.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.15.0...v3.15.1) (2026-02-17)


### Bug Fixes

* add naive datetime guards to fromisoformat() in Redis cache readers ([1b3e6f2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1b3e6f2f11c20aa240da1beb11dd7dfb20dbe6e8))
* add naive datetime guards to fromisoformat() in Redis cache readers ([6fa4948](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6fa49485d9f1cd678cb5f9fa7d0375fd47643239))

## [3.15.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.14.1...v3.15.0) (2026-02-17)


### New Features

* add LOG_COLORS env setting to toggle console ANSI colors ([27309f5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/27309f53d9fa0ba9a2ca07a65feed96bf38f470c))
* add web campaign links with bonus processing in auth flow ([d955279](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d9552799c17a76e2cc2118699528c5b591bd97fb))


### Bug Fixes

* AttributeError in withdrawal admin notification (send_to_admins → send_admin_notification) ([c75ec0b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c75ec0b22a3f674d3e1a24b9d546eca1998701b3))
* remove local UTC re-imports shadowing module-level import in purchase.py ([e68760c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e68760cc668016209f4f19a2e08af8680343d6ed))

## [3.14.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.14.0...v3.14.1) (2026-02-17)


### Bug Fixes

* add naive datetime guards to parsers and fix test datetime literals ([0946090](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/094609005af7358bf5d34d252fc66685bd25751c))
* address remaining abs() issues from review ([ff21b27](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ff21b27b98bb5a7517e06057eb319c9f3ebb74c7))
* complete datetime.utcnow() → datetime.now(UTC) migration ([eb18994](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eb18994b7d34d777ca39d3278d509e41359e2a85))
* normalize transaction amount signs across all aggregations ([4247981](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4247981c98111af388c98628c1e61f0517c57417))
* prevent negative amounts in spent display and balance history ([c30972f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c30972f6a7911a89a6c3f2080019ff465d11b597))

## [3.14.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.13.0...v3.14.0) (2026-02-16)


### New Features

* show all active webhook endpoints in startup log ([9d71005](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9d710050ad40ba76a14aa6ace8e8a47f25cdde94))


### Bug Fixes

* force basicConfig to replace pre-existing handlers ([7eb8d4e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7eb8d4e153bab640a5829f75bfa6f70df5763284))
* NameError in set_user_devices_button — undefined action_text ([1b8ef69](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1b8ef69a1bbb7d8d86827cf7aaa4f05cbf480d75))
* remove unused PaymentService from MonitoringService init ([491a7e1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/491a7e1c425a355e55b3020e2bcc7b96047bdf5e))
* resolve MissingGreenlet error when accessing subscription.tariff ([a93a32f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a93a32f3a7d1b259a2e24954ae5d2b7c966c5639))
* sync support mode from cabinet admin to SupportSettingsService ([516be6e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/516be6e600a08ad700d83b793dc64b2ca07bdf44))
* sync SUPPORT_SYSTEM_MODE between SystemSettings and SupportSettings ([0807a9f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0807a9ff19d1eb4f1204f7cbeb1da1c1cfefe83a))


### Refactoring

* improve log formatting — logger name prefix and table alignment ([f637204](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f63720467a935bdaaa58bb34d588d65e46698f26))

## [3.13.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.12.1...v3.13.0) (2026-02-16)


### New Features

* colored console logs via structlog + rich + FORCE_COLOR ([bf64611](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bf646112df02aa7aa7918d0513cb6968ceb7f378))


### Bug Fixes

* limit Rich traceback output to prevent console flood ([11ef714](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11ef714e0dde25a08711c0daeee943b6e71e20b7))
* resolve exc_info for admin notifications, clean log formatting ([11f8af0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11f8af003fc60384abafa2b670b89d6ad3ac57a4))
* suppress startup log noise (~350 lines → ~30) ([8a6650e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8a6650e57cd8ea396d9b057a7753469947f38d29))
* traceback in Telegram notifications + reduce log padding ([909a403](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/909a4039c43b910761bd05c36e79c8e6773199db))
* use sync context manager for structlog bound_contextvars ([25e8c9f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/25e8c9f8fc4d2c66d5a1407d3de5c7402dc596da))


### Refactoring

* complete structlog migration with contextvars, kwargs, and logging hardening ([1f0fef1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1f0fef114bd979b2b0d2bd38dde6ce05e7bba07b))

## [3.12.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.12.0...v3.12.1) (2026-02-16)


### Bug Fixes

* add /start burst rate-limit to prevent spam abuse ([61a9722](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/61a97220d30031816ab23e33a46717e4895c0758))
* add promo code anti-abuse protections ([97ec39a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/97ec39aa803f0e3f03fdcd482df0cbcb86fd1efd))
* handle TelegramBadRequest in ticket edit_message_text calls ([8e61fe4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8e61fe47746da2ac09c3ea8c4dbfc6be198e49e3))
* replace deprecated Query(regex=) with pattern= ([871ceb8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/871ceb866ccf1f3a770c7ef33406e1a43d0a7ff7))

## [3.12.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.11.0...v3.12.0) (2026-02-15)


### New Features

* add 'default' (no color) option for button styles ([10538e7](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/10538e735149bf3f3f2029ff44b94d11d48c478e))
* add button style and emoji support for cabinet mode (Bot API 9.4) ([bf2b2f1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bf2b2f1c5650e527fcac0fb3e72b4e6e19bef406))
* add per-button enable/disable toggle and custom labels per locale ([68773b7](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/68773b7e77aa344d18b0f304fa561c91d7631c05))
* add per-section button style and emoji customization via admin API ([a968791](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a9687912dfe756e7d772d96cc253f78f2e97185c))
* add web admin button for admins in cabinet mode ([9ac6da4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ac6da490dffa03ce823009c6b4e5014b7d2bdfb))
* rename MAIN_MENU_MODE=text to cabinet with deep-linking to frontend sections ([ad87c5f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad87c5fb5e1a4dd0ef7691f12764d3df1530f643))


### Bug Fixes

* daily tariff subscriptions stuck in expired/disabled with no resume path ([80914c1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/80914c1af739aa0ee1ea75b0e5871bf391b9020d))
* filter out traffic packages with zero price from purchase options ([64a684c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/64a684cd2ff51e663a1f70e61c07ca6b4f6bfc91))
* handle photo message in ticket creation flow ([e182280](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e1822800aba3ea5eee721846b1e0d8df0a9398d1))
* handle tariff_extend callback without period (back button crash) ([ba0a5e9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ba0a5e9abd9bd582968d69a5c6e57f336094c782))
* pre-validate CABINET_BUTTON_STYLE to prevent invalid values from suppressing per-section defaults ([46c1a69](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/46c1a69456036cb1be784b8d952f27110e9124eb))
* remove redundant trial inactivity monitoring checks ([d712ab8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d712ab830166cab61ce38dd32498a8a9e3e602b0))
* webhook notification 'My Subscription' button uses unregistered callback_data ([1e2a7e3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1e2a7e3096af11540184d60885b8c08d73506c4a))

## [3.11.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.3...v3.11.0) (2026-02-12)


### New Features

* add cabinet admin API for pinned messages management ([1a476c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1a476c49c19d1ec2ab2cda1c2ffb5fd242288bb6))
* add startup warnings for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE and MINIAPP_CUSTOM_URL ([476b89f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/476b89fe8e613c505acfc58a9554d31ccf92718a))


### Bug Fixes

* add passive_deletes to Subscription relationships to prevent NOT NULL violation on cascade delete ([bfd66c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bfd66c42c1fba3763f41d641cea1bd101ec8c10c))
* add startup warning for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE in guide mode ([1d43ae5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1d43ae5e25ffcf0e4fe6fec13319d393717e1e50))
* flood control handling in pinned messages and XSS hardening in HTML sanitizer ([454b831](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/454b83138e4db8dc4f07171ee6fe262d2cd6d311))
* suppress expired callback query error in AuthMiddleware ([2de4384](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2de438426a647e2bcae9b4d99eef4093ff8b5429))
* ticket creation crash and webhook PendingRollbackError ([760c833](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/760c833b7402541d3c7cf2ed7fc0418119e75042))

## [3.10.3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.2...v3.10.3) (2026-02-12)


### Bug Fixes

* handle unique constraint conflicts during backup restore without clear_existing ([5893874](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/589387477624691e0026086800428e7e52e06128))
* harden backup create/restore against serialization and constraint errors ([fc42916](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fc42916b10bb698895eb75c0e2568747647555d3))
* resolve deadlock on server_squads counter updates and add webhook notification toggles ([57dc1ff](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/57dc1ff47f2f6183351db7594544a07ca6f27250))

## [3.10.2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.1...v3.10.2) (2026-02-12)


### Bug Fixes

* allow email change for unverified emails ([93bb8e0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/93bb8e0eb492ca59e29da86594e84e9c486fea65))
* clean stale squad UUIDs from tariffs during server sync ([fcaa9df](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fcaa9dfb27350ceda3765c6980ad67f671477caf))
* delete subscription_servers before subscription to prevent FK violation ([7d9ced8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7d9ced8f4f71b43ed4ac798e6ff904a086e1ac4a))
* handle StaleDataError in webhook user.deleted server counter decrement ([c30c2fe](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c30c2feee1db03f0a359b291117da88002dd0fe0))
* handle time/date types in backup JSON serialization ([27365b3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/27365b3c7518c09229afcd928f505d0f3f66213f))
* HTML parse fallback, email change race condition, username length limit ([d05ff67](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d05ff678abfacaa7e55ad3e55f226d706d32a7b7))
* payment race conditions, balance atomicity, renewal rollback safety ([c5124b9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c5124b97b63eda59b52d2cbf9e2dcdaa6141ed6e))
* remove DisplayNameRestrictionMiddleware ([640da34](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/640da3473662cfdcceaa4346729467600ac3b14f))
* suppress bot-blocked-by-user error in AuthMiddleware ([fda9f3b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fda9f3beecbfcca4d7abc16cf661d5ad5e3b5141))
* UnboundLocalError for get_logo_media in required_sub_channel_check ([d3c14ac](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d3c14ac30363839d1340129f279a7a7b4b021ed1))
* use traffic topup config and add WATA 429 retry ([b5998ea](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b5998ea9d22644ed2914b0e829b3a76a32a69ddf))


### Refactoring

* remove modem functionality from classic subscriptions ([ee2e79d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ee2e79db3114fe7a9852d2cd33c4b4fbbde311ea))

## [3.10.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.0...v3.10.1) (2026-02-11)


### Bug Fixes

* address review issues in backup, updates, and webhook handlers ([2094886](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/20948869902dc570681b05709ac8d51996330a6e))
* allow purchase when recalculated price is lower than cached ([19dabf3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/19dabf38512ae0c2121108d0b92fc8f384292484))
* change CryptoBot URL priority to bot_invoice_url for Telegram opening ([3193ffb](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3193ffbd1bee07cb79824d87cb0f77b473b22989))
* clear subscription data when user deleted from Remnawave panel ([b0fd38d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b0fd38d60c22247a0086c570665b92c73a060f2f))
* downgrade Telegram timeout errors to warning in monitoring service ([e43a8d6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e43a8d6ce4c40a7212bf90644f82da109717bdcb))
* expand backup coverage to all 68 models and harden restore ([02e40bd](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/02e40bd6f7ef8e653cae53ccd127f2f79009e0d4))
* handle nullable traffic_limit_gb and end_date in subscription model ([e94b93d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e94b93d0c10b4e61d7750ca47e1b2f888f5873ed))
* handle StaleDataError in webhook when user already deleted ([d58a80f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d58a80f3eaa64a6fc899e10b3b14584fb7fc18a9))
* ignore 'message is not modified' on privacy policy decline ([be1da97](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/be1da976e14a35e6cca01a7fca7529c55c1a208b))
* preserve purchased traffic when extending same tariff ([b167ed3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b167ed3dd1c6e6239db2bdbb8424bcb1fb7715d9))
* prevent cascading greenlet errors after sync rollback ([a1ffd5b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a1ffd5bda6b63145104ce750835d8e6492d781dc))
* protect server counter callers and fix tariff change detection ([bee4aa4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bee4aa42842b8b6611c7c268bcfced408a227bc0))
* suppress 'message is not modified' error in updates panel ([3a680b4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3a680b41b0124848572809d187cab720e1db8506))
* use callback fallback when MINIAPP_CUSTOM_URL is not set ([eaf3a07](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eaf3a07579729031030308d77f61a5227b796c02))
* use flush instead of commit in server counter functions ([6cec024](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6cec024e46ef9177cb59aa81590953c9a75d81bb))

## [3.10.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.9.1...v3.10.0) (2026-02-10)


### New Features

* add all remaining RemnaWave webhook events (node, service, crm, device) ([1e37fd9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1e37fd9dd271814e644af591343cada6ab12d612))
* add close button to all webhook notifications ([d9de15a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d9de15a5a06aec3901415bdfd25b55d2ca01d28c))
* add MULENPAY_WEBSITE_URL setting for post-payment redirect ([fe5f5de](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fe5f5ded965e36300e1c73f25f16de22f84651ad))
* add RemnaWave incoming webhooks for real-time subscription events ([6d67cad](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6d67cad3e7aa07b8490d88b73c38c4aca6b9e315))
* handle errors.bandwidth_usage_threshold_reached_max_notifications webhook ([8e85e24](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8e85e244cb786fb4c06162f2b98d01202e893315))
* handle service.subpage_config_changed webhook event ([43a326a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/43a326a98ccc3351de04d9b2d660d3e7e0cb0efc))
* unified notification delivery for webhook events (email + WS support) ([26637f0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/26637f0ae5c7264c0430487d942744fd034e78e8))
* webhook protection — prevent sync/monitoring from overwriting webhook data ([184c52d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/184c52d4ea3ce02d40cf8a5ab42be855c7c7ae23))


### Bug Fixes

* add action buttons to webhook notifications and fix empty device names ([7091eb9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7091eb9c148aaf913c4699fc86fef5b548002668))
* add missing placeholders to Arabic SUBSCRIPTION_INFO template ([fe54640](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fe546408857128649930de9473c7cde1f7cc450a))
* allow non-HTTP deep links in crypto link webhook updates ([f779225](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f77922522a85b3017be44b5fc71da9c95ec16379))
* build composite device name from platform + hwid short suffix ([17ce640](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17ce64037f198837c8f2aa7bf863871f60bdf547))
* downgrade transient API errors (502/503/504) to warning level ([ec8eaf5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ec8eaf52bfdc2bde612e4fc0324575ba7dc6b2e1))
* extract device name from nested hwidUserDevice object ([79793c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/79793c47bbbdae8b0f285448d5f70e90c9d4f4b0))
* preserve payment initiation time in transaction created_at ([90d9df8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/90d9df8f0e949913f09c4ebed8fe5280453ab3ab))
* security and architecture fixes for webhook handlers ([dc1e96b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/dc1e96bbe9b4496e91e9dea591c7fc0ef4cc245b))
* stop CryptoBot webhook retry loop and save cabinet payments to DB ([2cb6d73](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2cb6d731e96cbfc305b098d8424b84bfd6826fb4))
* sync subscription status from panel in user.modified webhook ([5156d63](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5156d635f0b5bc0493e8f18ce9710cca6ff4ffc8))
* use event field directly as event_name (already includes scope prefix) ([9aa22af](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9aa22af3390a249d1b500d75a7d7189daaed265e))
* webhook:close button not working due to channel check timeout ([019fbc1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/019fbc12b6cf61d374bbed4bce3823afc60445c9))

## [3.9.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.9.0...v3.9.1) (2026-02-10)


### Bug Fixes

* don't delete Heleket invoice message on status check ([9943253](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/994325360ca7665800177bfad8f831154f4d733f))
* safe HTML preview truncation and lazy-load subscription fallback ([40d8a6d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/40d8a6dc8baf3f0f7c30b0883898b4655a907eb5))
* use actual DB columns for subscription fallback query ([f0e7f8e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f0e7f8e3bec27d97a3f22445948b8dde37a92438))

## [3.9.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.8.0...v3.9.0) (2026-02-09)


### New Features

* add lite mode functionality with endpoints for retrieval and update ([7b0403a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7b0403a307702c24efefc5c14af8cb2fb7525671))
* add Persian (fa) locale with complete translations ([29a3b39](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/29a3b395b6e67e4ce2437b75120b78c76b69ff4f))
* allow tariff deletion with active subscriptions ([ebd6bee](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ebd6bee05ed7d9187de9394c64dfd745bb06b65a))
* **localization:** add Persian (fa) locale support and wire it across app flows ([cc54a7a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/cc54a7ad2fb98fe6e662e1923027f4989ae72868))


### Bug Fixes

* nullify payment FK references before deleting transactions in user restoration ([0b86f37](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0b86f379b4e55e499ca3d189137e2aed865774b5))
* prevent sync from overwriting end_date for non-ACTIVE panel users ([49871f8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/49871f82f37d84979ea9ec91055e3f046d5854be))
* promo code max_uses=0 conversion and trial UX after promo activation ([1cae713](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1cae7130bc87493ab8c7691b3c22ead8189dab55))
* skip users with active subscriptions in admin inactive cleanup ([e79f598](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e79f598d17ffa76372e6f88d2a498accf8175c76))
* use selection.period.days instead of selection.period_days ([4541016](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/45410168afe683675003a1c41c17074a54ce04f1))


### Performance

* cache logo file_id to avoid re-uploading on every message ([142ff14](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/142ff14a502e629446be7d67fab880d12bee149d))


### Refactoring

* remove "both" mode from BOT_RUN_MODE, keep only polling and webhook ([efa3a5d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/efa3a5d4579f24dabeeba01a4f2e981144dd6022))
* remove Flask, use FastAPI exclusively for all webhooks ([119f463](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/119f463c36a95685c3bc6cdf704e746b0ba20d56))
* remove smart auto-activation & activation prompt, fix production bugs ([a3903a2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a3903a252efdd0db4b42ca3fd6771f1627050a7f))

## [3.8.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.2...v3.8.0) (2026-02-08)


### New Features

* add admin device management endpoints ([c57de10](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c57de1081a9e905ba191f64c37221c36713c82a6))
* add admin traffic packages and device limit management ([2f90f91](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2f90f9134df58b8c0a329c20060efcf07d5d92f9))
* add admin updates endpoint for bot and cabinet releases ([11b8ab1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11b8ab1959e83fafe405be0b76dfa3dd1580a68b))
* add endpoint for updating user referral commission percent ([da6f746](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/da6f746b093be8cdbf4e2889c50b35087fbc90de))
* add enrichment data to CSV export ([f2dbab6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f2dbab617155cdc41573d885f0e55222e5b9825b))
* add server-side sorting for enrichment columns ([15c7cc2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/15c7cc2a58e1f1935d10712a981466629db251d1))
* add system info endpoint for admin dashboard ([02c30f8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/02c30f8e7eb6ba90ed8983cfd82199a22b473bbf))
* add traffic usage enrichment endpoint with devices, spending, dates, last node ([5cf3f2f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5cf3f2f76eb2cd93282f845ea0850f6707bfcc09))
* admin panel enhancements & bug fixes ([e6ebf81](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e6ebf81752499df8eb0a710072785e3d603dba33))


### Bug Fixes

* add debug logging for bulk device response structure ([46da31d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/46da31d89c55c225dec9136d225f2db967cf8961))
* add email field to traffic table for OAuth/email users ([94fcf20](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/94fcf20d17c54efd67fa7bd47eff1afdd1507e08))
* add email/UUID fallback for OAuth user panel sync ([165965d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/165965d8ea60a002c061fd75f88b759f2da66d7d))
* add enrichment device mapping debug logs ([5be82f2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5be82f2d78aed9b54d74e86f261baa5655e5dcd9))
* include additional devices in tariff renewal price and display ([17e9259](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17e9259eb1d41dbf1d313b6a7d500f6458359393))
* paginate bulk device endpoint to fetch all HWID devices ([4648a82](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4648a82da959410603c92055bcde7f96131e0c29))
* read bot version from pyproject.toml when VERSION env is not set ([9828ff0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9828ff0845ec1d199a6fa63fe490ad3570cf9c8f))
* revert device pagination, add raw user data field discovery ([8f7fa76](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8f7fa76e6ab34a3ad2f61f4e1f06026fd3fbf4e3))
* use bulk device endpoint instead of per-user calls ([5f219c3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5f219c33e6d49b0e3e4405a57f8344a4237f1002))
* use correct pagination params (start/size) for bulk HWID devices ([17af51c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17af51ce0bdfa45197384988d56960a1918ab709))
* use per-user panel endpoints for reliable device counts and last node data ([9d39901](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9d39901f78ece55c740a5df2603601e5d0b1caca))

## [3.7.2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.1...v3.7.2) (2026-02-08)


### Bug Fixes

* handle FK violation in create_yookassa_payment when user is deleted ([55d281b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/55d281b0e37a6e8977ceff792cccb8669560945b))
* remove dots from Remnawave username sanitization ([d6fa86b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d6fa86b870eccbf22327cd205539dd2084f0014e))

## [3.7.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.0...v3.7.1) (2026-02-08)


### Bug Fixes

* release-please config — remove blocked workflow files ([d88ca98](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d88ca980ec67e303e37f0094a2912471929b4cef))
* remove workflow files and pyproject.toml from release-please extra-files ([5070bb3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5070bb34e8a09b2641783f5e818bb624469ad610))
* resolve HWID reset and webhook FK violation ([5f3e426](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5f3e426750c2adcb097b92f1a9e7725b1c5c5eba))
* resolve HWID reset context manager bug and webhook FK violation ([a9eee19](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a9eee19c95efdc38ecf5fa28f7402a2bbba7dd07))
* resolve merge conflict in release-please config ([0ef4f55](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0ef4f55304751571754f2027105af3e507f75dfd))
* resolve multiple production errors and performance issues ([071c23d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/071c23dd5297c20527442cb5d348d498ebf20af4))

## [3.7.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.6.0...v3.7.0) (2026-02-07)


### Features

* add admin traffic usage API ([aa1cd38](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/aa1cd3829c5c3671e220d49dd7ec2d83563e2cf9))
* add admin traffic usage API with per-node statistics ([6c2c25d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6c2c25d2ccb27446c822e4ed94d9351bfeaf4549))
* add node/status filters and custom date range to traffic page ([ad260d9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad260d9fe0b232c9d65176502476212902909660))
* add node/status filters, custom date range, connected devices to traffic page ([9ea533a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ea533a864e345647754f316bd27971fba1420af))
* add node/status filters, date range, devices to traffic page ([ad6522f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad6522f547e68ef5965e70d395ca381b0a032093))
* add risk columns to traffic CSV export ([7c1a142](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7c1a1426537e43d14eff0a1c3faeca484611b58b))
* add tariff filter, fix traffic data aggregation ([fa01819](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fa01819674b2d2abb0d05b470559b09eb43abef8))
* node/status filters + custom date range for traffic page ([a161e2f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a161e2f904732b459fef98a67abfaae1214ecfd4))
* tariff filter + fix traffic data aggregation ([1021c2c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1021c2cdcd07cf2194e59af7b59491108339e61f))
* traffic filters, date range & risk columns in CSV export ([4c40b5b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4c40b5b370616a9ab40cbf0cccdbc0ac4a3f8278))


### Bug Fixes

* close unclosed HTML tags in version notification ([0b61c7f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0b61c7fe482e7bbfbb3421307a96d54addfd91ee))
* close unclosed HTML tags when truncating version notification ([b674550](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b6745508da861af9b2ff05d89b4ac9a3933da510))
* correct response parsing for non-legacy node-users endpoint ([a076dfb](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a076dfb5503a349450b5aa8aac3c6f40070b715d))
* correct response parsing for non-legacy node-users endpoint ([91ac90c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/91ac90c2aecfb990679b3d0c835314dde448886a))
* handle mixed types in traffic sort ([eeed2d6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eeed2d6369b07860505c59bcff391e7b17e0ffb7))
* handle mixed types in traffic sort for string fields ([a194be0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a194be0843856b3376167d9ba8a8ef737280998c))
* resolve 429 rate limiting on traffic page ([b12544d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b12544d3ea8f4bbd2d8c941f83ee3ac412157adb))
* resolve 429 rate limiting on traffic page ([924d6bc](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/924d6bc09c815c1d188ea1d0e7974f7e803c1d3f))
* use legacy per-node endpoint for traffic aggregation ([cc1c8ba](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/cc1c8bacb42a9089021b7ae0fecd1f2717953efb))
* use legacy per-node endpoint with correct response format ([b707b79](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b707b7995b90c6465910a35e9a4403e1408c6568))
* use PaymentService for cabinet YooKassa payments ([61bb8fc](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/61bb8fcafd94509568f134ccdba7769b66cc7d5d))
* use PaymentService for cabinet YooKassa payments to save local DB record ([ff5bba3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ff5bba3fc5d1e1b08d008b64215e487a9eb70960))

## [3.6.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.5.0...v3.6.0) (2026-02-07)


### Features

* add OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([97be4af](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/97be4afbffd809fe2786a6d248fc4d3f770cb8cf))
* add panel info, node usage endpoints and campaign to user detail ([287a43b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/287a43ba6527ff3464a527821d746a68e5371bbe))
* add panel info, node usage endpoints and campaign to user detail ([0703212](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/070321230bcb868e4bc7a39c287ed3431a4aef4a))
* add TRIAL_DISABLED_FOR setting to disable trial by user type ([c4794db](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c4794db1dd78f7c48b5da896bdb2f000e493e079))
* add user_id filter to admin tickets endpoint ([8886d0d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8886d0dea20aa5a31c6b6f0c3391b3c012b4b34d))
* add user_id filter to admin tickets endpoint ([d3819c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d3819c492f88794e4466c2da986fd3a928d7f3df))
* block registration with disposable email addresses ([9ca24ef](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ca24efe434278925c0c1f8d2f2d644a67985c89))
* block registration with disposable email addresses ([116c845](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/116c8453bb371b5eacf5c9d07f497eb449a355cc))
* disable trial by user type (email/telegram/all) ([4e7438b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4e7438b9f9c01e30c48fcf2bbe191e9b11598185))
* migrate OAuth state storage from in-memory to Redis ([e9b98b8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e9b98b837a8552360ef4c41f6cd7a5779aa8b0a7))
* OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([3cbb9ef](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3cbb9ef024695352959ef9a82bf8b81f0ba1d940))
* return 30-day daily breakdown for node usage ([7102c50](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7102c50f52d583add863331e96f3a9de189f581a))
* return 30-day daily breakdown for node usage ([e4c65ca](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e4c65ca220994cf08ed3510f51d9e2808bb2d154))


### Bug Fixes

* increase OAuth HTTP timeout to 30s ([333a3c5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/333a3c590120a64f6b2963efab1edd861274840c))
* parse bandwidth stats series format for node usage ([557dbf3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/557dbf3ebe777d2137e0e28303dc2a803b15c1c6))
* parse bandwidth stats series format for node usage ([462f7a9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/462f7a99b9d5c0b7436dbc3d6ab5db6c6cfa3118))
* pass tariff object instead of tariff_id to set_tariff_promo_groups ([1ffb8a5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1ffb8a5b85455396006e1fcddd48f4c9a2ca2700))
* query per-node legacy endpoint for user traffic breakdown ([b94e3ed](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b94e3edf80e747077992c03882119c7559ad1c31))
* query per-node legacy endpoint for user traffic breakdown ([51ca3e4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/51ca3e42b75c1870c76a1b25f667629855cfe886))
* reduce node usage to 2 API calls to avoid 429 rate limit ([c68c4e5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c68c4e59846abba9c7c78ae91ec18e2e0e329e3c))
* reduce node usage to 2 API calls to avoid 429 rate limit ([f00a051](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f00a051bb323e5ba94a3c38939870986726ed58e))
* use accessible nodes API and fix date format for node usage ([943e9a8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/943e9a86aaa449cd3154b0919cfdc52d2a35b509))
* use accessible nodes API and fix date format for node usage ([c4da591](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c4da59173155e2eeb69eca21416f816fcbd1fa9c))

## [3.5.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.4.0...v3.5.0) (2026-02-06)


### Features

* add tariff reorder API endpoint ([4c2e11e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4c2e11e64bed41592f5a12061dcca74ce43e0806))
* pass platform-level fields from RemnaWave config to frontend ([095bc00](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/095bc00b33d7082558a8b7252906db2850dce9da))
* serve original RemnaWave config from app-config endpoint ([43762ce](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/43762ce8f4fa7142a1ca62a92b97a027dab2564d))
* tariff reorder API endpoint ([085a617](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/085a61721a8175b3f4fd744614c446d73346f2b7))


### Bug Fixes

* enforce blacklist via middleware ([561708b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/561708b7772ec5b84d6ee049aeba26dc70675583))
* enforce blacklist via middleware instead of per-handler checks ([966a599](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/966a599c2c778dce9eea3c61adf6067fb33119f6))
* exclude signature field from Telegram initData HMAC validation ([5b64046](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5b6404613772610c595e55bde1249cdf6ec3269d))
* improve button URL resolution and pass uiConfig to frontend ([0ed98c3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0ed98c39b6c95911a38a26a32d0ffbcf9cfd7c80))
* restore unquote for user data parsing in telegram auth ([c2cabbe](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c2cabbee097a41a95d16c34d43ab7e70d076c4dc))


### Reverts

* remove signature pop from HMAC validation ([4234769](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4234769e92104a6c4f8f1d522e1fca25bc7b20d0))
