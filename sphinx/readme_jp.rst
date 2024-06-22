===========
ReadMe |ja|
===========

このモジュールは :mod:`asyncgui` を用いるプログラム向けのタイマー機能を提供します。
機能は大別するとコールバック型とasync/await型に分けられ、状況に応じて好きな方を使えます。

まずはコールバック型のAPIを用いた以下のコードを見てください。

.. code-block::

    from asyncgui_ext.clock import Clock

    clock = Clock()

    # 20経過後に関数が呼ばれるようにする。
    clock.schedule_once(lambda dt: print("Hello"), 20)

    # 時計を10進める。
    clock.tick(10)

    # 合計で20進むので関数が呼ばれる。
    clock.tick(10)  # => Hello

:mod:`sched` と同じで時間の単位が決まってない事に気付いたと思います。
APIに渡す時間の単位は統一さえされていれば何でも構いません。

次はasync/await型のAPIを用いた以下のコードを見てください。

.. code-block::

    import asyncgui
    from asyncgui_ext.clock import Clock

    clock = Clock()

    async def async_fn():
        await clock.sleep(20)
        print("Hello")

    asyncgui.start(async_fn())
    clock.tick(10)
    clock.tick(10)  # => Hello

この様に ``clock.tick()`` を呼ぶ事で時計内部の時が進み、関数が呼ばれたり停止中のタスクが再開するわけです。
しかしこれらの例はこのモジュールの仕組みを示しているだけであまり実用的ではありません。
実際のプログラムでは ``clock.tick()`` をループ内で呼んだり別のタイマーを用いて定期的に呼ぶ事になると思います。
例えば ``PyGame`` を使っているなら以下のように、

.. code-block::

    clock = pygame.time.Clock()
    vclock = asyncgui_ext.clock.Clock()

    # メインループ
    while running:
        ...

        dt = clock.tick(fps)
        vclock.tick(dt)

``Kivy`` を使っているなら以下のようになるでしょう。

.. code-block::

    from kivy.clock import Clock

    vclock = asyncui_ext.clock.Clock()
    Clock.schedule_interval(vclock.tick, 0)

インストール方法
-----------------------

マイナーバージョンまでを固定してください。

::

    poetry add asyncgui-ext-clock@~0.3
    pip install "asyncgui-ext-clock>=0.3,<0.4"

テスト環境
-----------------------

* CPython 3.10
* CPython 3.11
* CPython 3.12

その他
-----------------------

* [YouTube](https://youtu.be/kPVzO8fF0yg) (Kivy上で使う例)
