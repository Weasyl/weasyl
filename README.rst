Welcome to Weasyl!
==================

.. highlight:: console

`Weasyl`_ is a social gallery website designed for artists, writers, musicians,
and more to share their work with other artists and fans. We seek to bring the
creative world together in one easy to use, friendly, community website.


Quickstart
----------

The easiest way to get Weasyl running is within a virtual environment using
`Vagrant`_ (1.6 or greater) with `VirtualBox`_ (4.3.16 or greater). From inside the
``weasyl`` directory, simply run::

  $ make setup-vagrant

After libweasyl is cloned, Vagrant will fetch the base box and then provision
the VM. Expect this step to take a while as it downloads a virtual machine
image, installs all of weasyl's dependencies, and populates a small database.

To start the server inside the VM, run::

  $ make guest-run

Weasyl will then start running on <https://lo.weasyl.com:8443/>.


Next Steps
----------

At this point weasyl is running within a virtual machine. Your weasyl repo
is mounted as `/home/vagrant/weasyl` inside the guest so edits made locally
will be reflected inside the VM. To make changes, stop the `make guest-run`
process, edit the code, and rerun `make guest-run`.

If you need to examine the virtual machine (e.g. to look at the database
directly), run `vagrant ssh`.


The Sample Database
-------------------

The downloaded database contains sample content pulled and scrubbed from
weasyl staff accounts. No content should be included from non-staff users
or those who haven't otherwise explicitly given permission to use their
account.

For privacy and technical reasons, not all content is included: Hidden
submissions, private messages, journals, hidden favorites, notifications,
and similar things have been removed. If you want to develop around such
functionality, they will have to be added manually.

All passwords in the database have been set to 'password'.


Troubleshooting and Getting Help
--------------------------------

If the `make setup-vagrant` step fails halfway through, you can resume it with the
standard vagrant commands `vagrant up` followed by `vagrant provision`.

If you have questions or get stuck, you can trying talking to weasyl project members in
the project's `gitter room <https://gitter.im/Weasyl/weasyl>`_.

The above instructions have been tested on Linux and OS X. It should be possible
to run weasyl in a virtual environment under Windows, but it hasn't been thoroughly
tested.


.. _Weasyl: https://www.weasyl.com
.. _Vagrant: https://www.vagrantup.com
.. _VirtualBox: https://www.virtualbox.org
