# CHANGELOG


## v0.8.0 (2025-10-21)

### Features

- Add support for updating the lsp workspace settings
  ([`85e6b10`](https://github.com/bec-project/qtmonaco/commit/85e6b10495e3818a11d2a359759343b266e5be0a))


## v0.7.1 (2025-10-10)

### Bug Fixes

- **model**: Only create a new model if language or uri changes
  ([`62c68ec`](https://github.com/bec-project/qtmonaco/commit/62c68eca10d19f67477eabe3bce7fc6e3cb2f96a))

### Documentation

- Add movie to README
  ([`4aa4b2a`](https://github.com/bec-project/qtmonaco/commit/4aa4b2a6e77bfbd78362a79b86e426337cd5e49d))

Added an output image to the README for better visualization.


## v0.7.0 (2025-09-01)

### Features

- Add set line number mode option
  ([`414c1eb`](https://github.com/bec-project/qtmonaco/commit/414c1eb90df0c651cbdeafbc1aa8ed0677206b69))


## v0.6.0 (2025-08-31)

### Bug Fixes

- Add status bar for vim; otherwise some features do not work
  ([`4cca2fa`](https://github.com/bec-project/qtmonaco/commit/4cca2fae9041442fffd7b3ff45dcde45c471d2bf))

- Remove debugging print
  ([`3a56dc9`](https://github.com/bec-project/qtmonaco/commit/3a56dc928a80202b55608c19c52ac69d2f9512b9))

- Simplify completion provider
  ([`db361ab`](https://github.com/bec-project/qtmonaco/commit/db361abebbd1884150341e53f816a9a57cd19a6d))

- Update existing model unless a new file is specified
  ([`8ac7297`](https://github.com/bec-project/qtmonaco/commit/8ac7297eb0cc826d326292bc00a4269e6157d195))

### Features

- Add option for adding custom context menu actions
  ([`83d1985`](https://github.com/bec-project/qtmonaco/commit/83d198529ea91dee2575c4529e681890ca52e56e))

- Add support for model uris
  ([`6ac4758`](https://github.com/bec-project/qtmonaco/commit/6ac4758b041d8afb5e058d92658e6116c51a802f))

- Add support for receiving signature notifications
  ([`af9ffc0`](https://github.com/bec-project/qtmonaco/commit/af9ffc00ad7bfcad256674e373a0b3628d208cfa))

- First version with support for snippets
  ([`ac21838`](https://github.com/bec-project/qtmonaco/commit/ac21838613fbe109eced3d8dd122a2a5814db091))

- Generalize editor updates; add option to disable scroll beyond last line
  ([`e0fc4e2`](https://github.com/bec-project/qtmonaco/commit/e0fc4e2996b048b9329bca864564e3d1f0ecc787))

### Refactoring

- Move providers to separate module
  ([`a95642e`](https://github.com/bec-project/qtmonaco/commit/a95642ed9578b8f648d191a2e2d5220567196fe4))


## v0.5.1 (2025-08-12)

### Bug Fixes

- **readme**: Pyqt6 typo
  ([`57a7eb0`](https://github.com/bec-project/qtmonaco/commit/57a7eb097e8125c4b7345a7f5b8a533fd640eb7a))

### Build System

- Pyside6 upgraded to 6.9.0
  ([`a1e07b6`](https://github.com/bec-project/qtmonaco/commit/a1e07b67b6f363306f20309d1db2bc16a3cad8e9))


## v0.5.0 (2025-07-25)

### Features

- Add options to insert and delete lines
  ([`4143473`](https://github.com/bec-project/qtmonaco/commit/414347364a69622e852f7bd55482f8c7e525b437))

- **lsp**: Add option to set a hidden header
  ([`60cb2e9`](https://github.com/bec-project/qtmonaco/commit/60cb2e97069d15bf6023f856347a385f09410136))


## v0.4.1 (2025-07-18)

### Bug Fixes

- Remove backend from build
  ([`cc38340`](https://github.com/bec-project/qtmonaco/commit/cc3834088ae08d659e98bdd75dd091a8dc1c471a))


## v0.4.0 (2025-07-18)

### Features

- **vim**: Add vim mode
  ([`e870c83`](https://github.com/bec-project/qtmonaco/commit/e870c832de256729b6c1ec1fcc80e11618dc54ff))

### Refactoring

- Restructure repo
  ([`89e49cb`](https://github.com/bec-project/qtmonaco/commit/89e49cbd526fb7d2783fe3307d1de296a166e5af))


## v0.3.0 (2025-07-17)

### Features

- Add line highlighting feature
  ([`da269af`](https://github.com/bec-project/qtmonaco/commit/da269af11e450c33c610b7f7f34d5aec5a97d227))


## v0.2.3 (2025-07-16)

### Bug Fixes

- Add get_text method to retrieve current editor value; cleanup properties
  ([`24bb58a`](https://github.com/bec-project/qtmonaco/commit/24bb58a7b57132037e0d4d4460d8cf6c14426fce))


## v0.2.2 (2025-07-16)

### Bug Fixes

- Set js log to debugging
  ([`23301e1`](https://github.com/bec-project/qtmonaco/commit/23301e15d12a3d6b19f8571c5d492da62cca5472))


## v0.2.1 (2025-07-16)

### Bug Fixes

- Fix js mapping and cleanup
  ([`97ab296`](https://github.com/bec-project/qtmonaco/commit/97ab296db83b3cde8dc093360272d1f384fd84a2))

### Documentation

- Update readme with public api
  ([`b6c513f`](https://github.com/bec-project/qtmonaco/commit/b6c513f42bedb8ad006df0aa161c34d838831666))


## v0.2.0 (2025-07-16)

### Bug Fixes

- Fix js interface
  ([`5a32eec`](https://github.com/bec-project/qtmonaco/commit/5a32eec78440ff9b9abb73a2ae53aa5f47494f09))

### Features

- Add method to enable / disable the minimap
  ([`d89b6a8`](https://github.com/bec-project/qtmonaco/commit/d89b6a84c8ba6e68e99dca65b5567d289e00848b))


## v0.1.6 (2025-07-16)

### Bug Fixes

- Build js artifacts and include them in the release
  ([`8d5df31`](https://github.com/bec-project/qtmonaco/commit/8d5df31bbf1907a300a259c7d99869ba78032254))


## v0.1.5 (2025-07-11)

### Bug Fixes

- Update resource handling and build configuration for RCC files
  ([`72ea277`](https://github.com/bec-project/qtmonaco/commit/72ea277051f6d0920876fd826ffd65067a94b516))


## v0.1.4 (2025-07-11)

### Bug Fixes

- Remove unnecessary command from rcc file build step
  ([`92f3901`](https://github.com/bec-project/qtmonaco/commit/92f390178a75dcc45433af0d64fe6e69c9c6e4b7))

- Update build configuration to include all files and specify artifacts
  ([`dac680b`](https://github.com/bec-project/qtmonaco/commit/dac680bbb565fe25623ddc53c766d7468567e180))

### Continuous Integration

- Add debugging output
  ([`bfc4dc7`](https://github.com/bec-project/qtmonaco/commit/bfc4dc75854d4a9c021af590759cb4722314d601))


## v0.1.3 (2025-07-11)

### Bug Fixes

- Build
  ([`33d5d70`](https://github.com/bec-project/qtmonaco/commit/33d5d70b0952e24cb693532f112aa42b4e4ef9fa))


## v0.1.2 (2025-07-11)

### Bug Fixes

- Fix rcc location within build
  ([`31e288f`](https://github.com/bec-project/qtmonaco/commit/31e288f4d2b2c4d7f5872616183a2db5d07a68c2))


## v0.1.1 (2025-07-11)

### Bug Fixes

- Fix release step
  ([`182c7de`](https://github.com/bec-project/qtmonaco/commit/182c7dec74c46437e1a56d03c53b9992b135ad90))


## v0.1.0 (2025-07-11)

### Continuous Integration

- Add pypi build and upload
  ([`25ea54a`](https://github.com/bec-project/qtmonaco/commit/25ea54a80e6fd54a215cb3679ca80e8e49c8e97b))

- Init
  ([`0b5ef18`](https://github.com/bec-project/qtmonaco/commit/0b5ef1858bc95ec93e6c8abb993b1e01f8772cac))

### Features

- Add qt bridge
  ([`7361271`](https://github.com/bec-project/qtmonaco/commit/73612710b57424234900863606fe3aa74ad6754f))
