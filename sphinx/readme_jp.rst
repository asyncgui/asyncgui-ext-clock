===========
ReadMe |ja|
===========

このモジュールは :mod:`asyncgui` を用いるプログラム向けのタイマー機能を提供します。

.. code-block::

    import asyncgui
    from asyncgui_ext.clock import Clock

    clock = Clock()

    async def async_fn():
        await clock.sleep(20)  # 時間が20経過するのを待つ。
        print("Hello")

    asyncgui.start(async_fn())
    clock.tick(10)  # 時間が10進む。
    clock.tick(10)  # 合計で20進むのでタスクが再開し 'Hello' が表示される。

この様に ``clock.tick()`` を呼ぶ事で時計内部の時が進み停止中のタスクが再開するわけです。
また :mod:`sched` と同じで時間の単位が決まってない事に気付いたと思います。
APIに渡す時間の単位は統一さえされていれば何でも構いません。

ただ上記の例はこのモジュールの仕組みを示しているだけであり実用的な使い方ではありません。
実際のプログラムでは ``clock.tick()`` をメインループ内で呼んだり別のタイマーを用いて定期的に呼ぶ事になると思います。
例えば ``PyGame`` を使っているなら以下のように、

.. code-block::

    pygame_clock = pygame.time.Clock()
    clock = asyncgui_ext.clock.Clock()

    # メインループ
    while running:
        ...

        dt = pygame_clock.tick(fps)
        clock.tick(dt)

``Kivy`` を使っているなら以下のようになるでしょう。

.. code-block::

    from kivy.clock import Clock

    clock = asyncui_ext.clock.Clock()
    Clock.schedule_interval(clock.tick, 0)

インストール方法
-----------------------

マイナーバージョンまでを固定してください。

::

    poetry add asyncgui-ext-clock@~0.4
    pip install "asyncgui-ext-clock>=0.4,<0.5"

テスト環境
-----------------------

* CPython 3.10
* CPython 3.11
* CPython 3.12

その他
-----------------------

* `YouTube <https://youtu.be/kPVzO8fF0yg>`__ (Kivy上で使う例)
