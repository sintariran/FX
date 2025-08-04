# パッケージ作成設定

FXシステムのパッケージ作成に関する設定項目（04_実行.xlsmより）

## 共通設定

| 項目名 | 説明 | デフォルト値 |
|--------|------|-------------|
| AXIS_PERIOD | 軸時間足 | 1 |
| OUT_PAIR | 通貨 | 1 |
| PKG_ROOT_DIR | PKG参照・出力フォルダ | C:\Watch\operation_bktest_ver2\20_Package |
| SETTING_PATH_EDIT | 設定ファイルパス | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\07_設定更新.xlsm |
| SETTING_ROOT_DIR | 設定ファイルルートディレクトリ | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\30_Setting\20_Config |
| WORK_DIR | ワークディレクトリ | C:\Watch\operation_bktest_ver2\20_Package\work |
| INPUT_CHECK_DIR | チェックログディレクトリ | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\10_Log\60_チェック関連 |
| NESL_SETTING_PATH | nesl_settingファイルパス | C:\Watch\operation_bktest_ver2\90_ツール\上下計算Java\setting_include_scode_1\nesl_setting.csv |
| START_DATE | 対象開始日付 | 2019-10-07 |
| END_DATE | 対象終了日付 | 2019-10-11 |
| START_TIME | 対象開始時間 | 00:00:00 |
| END_TIME | 対象終了時間 | 23:59:00 |

## パッケージ出力設定

| 項目名 | 説明 | デフォルト値 |
|--------|------|-------------|
| MAX_RESIZE_PERIOD | 最大相対時間足 | 6 |
| PARA_VBS_DIR | パラ出力VBSディレクトリ | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\30_Setting\50_PKG作成パラ処理 |
| PARA_PROC_SWITH | パラで出力 | OFF |
| PKG_LOG_DIR | ログ出力ディレクトリ | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\10_Log\10_PKG出力関連 |
| HISTROY_PATH | PKG作成履歴ファイルパス | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\10_Log\10_PKG出力関連\パッケージ作成履歴.csv |
| OLD_NEW_CONFIG_TABLE | 設定ファイル読込対象パス | C:\Watch\operation_bktest_ver2\10_FX\20_ルートによるパッケージ作成\30_Setting\30_BT\設定情報読込対象.csv |
| PARENT_PKG_SWITCH | 親階層出力 | OFF |
| CHILD_PKG_SWITCH | 子階層出力 | OFF |
| OTHER_TERM_SWITCH | 周期同時出力 | ON |
| OTHER_TERM_TARGET | 同時出力周期（/区切り） | 0/1/5/6 |
| ALREADY_EXIST_SWITCH | 出力済みPKGは再出力しない | OFF |
| NO_CHANGE_ROUTE | 変更なしルート以降出力しない | OFF |
| COMBINE_DATE_SWITCH | 日付連結PKGを出力する | OFF |
| INPUT_CHECK_SWITCH | 入力チェック | OFF |
| PROCESS_CHECK_SWITCH | 処理チェック | OFF |
| HIERARCHY_CHECK_SWITCH | 階層チェック | OFF |

## バージョン情報

- オペレーション作成: 2.2
- パッケージ作成: 2.2
- パッケージ作成1day: 2.1
- パッケージ作成1min: 2
- 取引結果出力: 2
- 帰納法指標評価: 2
- 共通ライブラリ: 2
- 宣言: 2.2

## 出力対象

- 191^21-18
- 291^21-18
- 391^21-18
- 491^21-18
- 591^21-18
- 691^21-18