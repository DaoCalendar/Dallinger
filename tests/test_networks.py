from wallace import networks, agents, db, sources, models


class TestNetworks(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def test_create_network(self):
        net = models.Network()
        assert isinstance(net, models.Network)

    def test_network_agents(self):
        net = networks.Network()
        assert len(net.agents) == 0

        agent = agents.Agent()
        self.db.add(agent)
        self.db.commit()

        net.add_agent(agent)

        assert net.agents == [agent]

    def test_network_sources(self):
        net = networks.Network()
        self.db.add(net)

        assert len(net.sources) == 0

        source = sources.Source()
        source.network = net
        self.db.add(source)
        self.db.commit()

        assert net.sources == [source]

    def test_network_vectors(self):
        net = networks.Network()
        self.db.add(net)

        assert len(net.vectors) == 0

        agent1 = agents.Agent()
        agent2 = agents.Agent()
        self.db.add_all([agent1, agent2])

        net.add_agent(agent1)
        net.add_agent(agent2)
        vector = agent1.connect_to(agent2)
        vector.network = net
        self.db.add(vector)
        self.db.commit()

        assert len(net.vectors) == 1
        assert net.vectors[0].origin == agent1
        assert net.vectors[0].destination == agent2

    # def test_network_get_degrees(self):  # FIXME
    #     net = networks.Network()
    #     agent1 = agents.Agent()
    #     agent2 = agents.Agent()
    #     self.db.add_all([agent1, agent2])
    #     self.db.commit()

    #     assert net.get_degrees() == [0, 0]

    #     agent1.connect_to(agent2)
    #     self.db.commit()

    #     assert net.get_degrees() == [1, 0]

    def test_network_add_source_global(self):
        net = networks.Network()
        self.db.add(net)
        self.db.commit()

        agent1 = agents.Agent()
        agent2 = agents.Agent()
        self.db.add_all([agent1, agent2])

        # Add agents to network.
        net.add_agent(agent1)
        net.add_agent(agent2)

        source = sources.RandomBinaryStringSource()
        self.db.add(source)
        vectors = net.add_source_global(source)
        self.db.add_all(vectors)

        assert len(net.vectors) == 2
        # assert net.get_degrees() == [0, 0]  # FIXME
        # assert net.sources[0].outdegree == 2

    def test_network_add_source_local(self):
        net = networks.Network()
        agent1 = agents.Agent()
        agent2 = agents.Agent()
        self.db.add_all([agent1, agent2])
        self.db.commit()

        source = sources.RandomBinaryStringSource()
        net.add_source_local(source, agent1)

        assert len(net.vectors) == 1
        # assert net.get_degrees() == [0, 0]  # FIXME
        # assert net.sources[0].outdegree == 1

    def test_network_add_agent(self):
        net = networks.Network()
        self.db.add(net)
        self.db.commit()

        agent1 = agents.Agent()
        agent2 = agents.Agent()
        agent3 = agents.Agent()
        self.db.add_all([agent1, agent2, agent3])
        self.db.commit()

        net.add_agent(agent1)
        net.add_agent(agent2)
        net.add_agent(agent3)

        assert len(net.agents) == 3
        assert len(net.vectors) == 0
        assert len(net.sources) == 0

    def test_network_repr(self):
        net = networks.Network()
        self.db.add(net)

        agent1 = agents.Agent()
        agent2 = agents.Agent()
        self.db.add_all([agent1, agent2])

        net.add_agent(agent1)
        net.add_agent(agent2)

        source = sources.RandomBinaryStringSource()
        self.db.add(source)

        vectors = net.add_source_global(source)
        self.db.add_all(vectors)

        assert repr(net)[:8] == "<Network"
        assert repr(net)[15:] == "-base with 2 agents, 1 sources, 2 vectors>"

    def test_create_chain(self):
        net = networks.Chain()
        for i in range(4):
            agent = agents.Agent()
            self.db.add(agent)
            self.db.commit()
            net.add_agent(agent)

        source = sources.RandomBinaryStringSource()
        net.add_source_local(source, net.agents[0])

        assert len(net.agents) == 4
        assert len(net.sources) == 1
        assert len(net.vectors) == 4

    def test_chain_repr(self):
        net = networks.Chain()
        self.db.add(net)

        for i in range(4):
            agent = agents.Agent()
            self.db.add(agent)
            self.db.commit()
            net.add_agent(agent)

        source = sources.RandomBinaryStringSource()
        self.db.add(source)

        vectors = net.add_source_local(source, net.agents[0])
        self.db.add_all(vectors)

        assert repr(net)[:9] == "<Network-"
        assert repr(net)[15:] == "-chain with 4 agents, 1 sources, 4 vectors>"

    def test_create_fully_connected(self):
        net = networks.FullyConnected()
        for i in range(4):
            agent = agents.Agent()
            self.db.add(agent)
            new_vectors = net.add_agent(agent)
            self.db.add_all(new_vectors)

        assert len(net.agents) == 4
        assert len(net.vectors) == 12
        # assert net.get_degrees() == [3, 3, 3, 3]  # FIXME

    def test_fully_connected_repr(self):
        net = networks.FullyConnected()
        self.db.add(net)
        for i in range(4):
            agent = agents.Agent()
            self.db.add(agent)
            new_vectors = net.add_agent(agent)
            self.db.add_all(new_vectors)

        assert repr(net)[:9] == "<Network-"
        assert repr(net)[15:] == ("-fully-connected with 4 agents"
                                  ", 0 sources, 12 vectors>")

    def test_create_scale_free(self):
        net = networks.ScaleFree(m0=4, m=4)
        self.db.add(net)

        for i in range(4):
            agent = agents.Agent()
            self.db.add(agent)
            new_vectors = net.add_agent(agent)
            self.db.add_all(new_vectors)

        assert len(net.agents) == 4
        assert len(net.vectors) == 12
        agent1 = agents.Agent()
        net.add_agent(agent1)
        assert len(net.agents) == 5
        assert len(net.vectors) == 20
        agent2 = agents.Agent()
        net.add_agent(agent2)
        assert len(net.agents) == 6
        assert len(net.vectors) == 28

    def test_scale_free_repr(self):
        net = networks.ScaleFree(m0=4, m=4)
        self.db.add(net)

        for i in range(6):
            agent = agents.Agent()
            self.db.add(agent)
            new_vectors = net.add_agent(agent)
            self.db.add_all(new_vectors)

        assert repr(net)[:9] == "<Network-"
        assert repr(net)[15:] == ("-scale-free with 6 agents, "
                                  "0 sources, 28 vectors>")
