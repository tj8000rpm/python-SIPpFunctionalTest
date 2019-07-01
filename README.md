# python-SIPpFunctionalTest

## SIPp の実行をメインにSIPの機能試験を行うためのTemplate

Python の unittest を利用して SIPp を実行
SIPの信号を message log から取得し各種確認を行うサンプルプログラム



## 解説

### コードを抜粋

```python
    def test_case_1_1_sip_return_code(self):
        testcase_name = inspect.currentframe().f_code.co_name

        # SIPメッセージのログファイル名を定義する
        # ログファイルは後述するSIPpの呼び出し関数や、tearDownから呼び出せるように
        # TestCaseのメンバ変数としてデザイン
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), testecase_name)

        # SIPpに入力するインジェクションファイル(-infオプション)のファイル名定義し
        # リストで渡したCSVファイルの内容を（二次元リスト）ヘルパ関数である SIPp.helper_create_injection で作成し
        # 同じくヘルパ関数である SIPp.helper_write_injection_file 関数で定義したファイル名に書き出す
        # メッセージログと同様にSIPpの呼び出し関数等から呼べるようにメンバ変数として定義
        self.injectionfile = '{}/inputs/inf_{}.csv'.format(os.getcwd(), testcase_name)
        SIPp.helper_write_injection_file(SIPp.helper_create_injection(content=[['user1', 'Joe']]),
                                         path_to_file=self.injectionfile)

        # SIPpを各種オプションを指定して実行詳しくは後段に記述
        # SIPのシーケンスレベルの正しさはSIPpで確認することとする(return codeの評価)
        self.helper_run_sipp_test_case_1()

        # SIPp のSIPメッセージログからSIPの信号レベルでの確からしさを評価する
        # SIPpMessage クラスにより、SIPpが吐き出すログをパースした結果を保持し
        # さらにSIPpMessageクラスに定義してある各種ヘルパ関数や
        # メンバ関数を用いてSIPのメッセージをパースし、期待値と評価する
        # 本例ではSIPメッセージログファイルから SIPpMessage クラスのリストである messages を返す
        # SIPpMessage.parseMessagesFromLogfile 関数を用いてリストを取得後、
        # SIPpMessage.messagesFilter 関数を用いて更に、受信方向の信号のみにフィルタした 結果を messages に格納している
        messages = SIPpMessage.messagesFilter(SIPpMessage.parseMessagesFromLogfile(self.logfile), direction='received')

        # フィルタした受信方向のフィルタから、最後のSIP信号要素を取得し、
        # .getStatusCode メンバ関数を用いて SIPの最終レスポンスコードを取得し、期待値である200と比較している
        self.assertEqual(messages[-1].getStatusCode(), 200, 'Last Status code should be 200')
```

```python
    def helper_run_sipp_test_case_1(self):
        # Subprocessを用いてSIPpを実行するヘルパ関数を用いてSIPpを実行する
        # 実行結果として、Subprocessの実行結果 ret と 実行時に投入した sipp コマンドの内容 command を戻り値として受け取る。
        # 本プログラムはSIPpをシングルスレッドで実行するため、受信側の試験を行いたい場合はシナリオを工夫するか、
        # もしくはマルチスレッドで動く用に改変が必要
        # remote_host がsippでの接続先の指定 (uac時の必須パラメータ)
        # scenario_file がシナリオXMLの指定(sfオプション)
        # request_service がRequestURIのユーザ部指定 (sオプション)
        # injection_file がインジェクションファイルの指定（infオプション）
        # bind_sip_addr がSIPで待受け、送信するIPアドレス（iオプション）
        # bind_sip_port がSIPで待受け、送信するポート番号（pオプション）
        # logfile_path がSIPメッセージログの出力先指定（trace_msg/message_fileオプション）
        ret, command = SIPp.helper_run_a_sipp(remote_host='localhost:5062', scenario_file='tests/scenarios/uac-uas.xml',
                                              request_service='0312341234', injection_file=self.injectionfile,
                                              bind_sip_addr='127.0.0.1', bind_sip_port=5062,
                                              logfile_path=self.logfile)

        # SIPp　プログラムの実行結果による戻り値を評価している
        # timeout プログラムを用いて時限付きで実行しているため、もし想定以上に処理に時間がかかり（例えば再送を繰り返しているなど）
        # 正常に処理できなかった場合はtimeoutが発生し、結果として戻り値には124が入るため、まず124と比較し、タイムアウトしていないかを評価する
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')

        # 次に戻り値を0で比較し、0以外の終了コードであった場合は中断する。
        # SIPpが正しく、シナリオどおり終了した場合は0が帰るため、シーケンスレベル（信号順序等）の確からしさの担保は本比較を持って行える。
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')
```
